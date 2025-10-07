import copy
import json
import logging
import yaml
import argparse
from kubernetes import client, config

def ensure_path_exists(config, path):
    """
    Recursively ensure that a given path exists in the config.
    """
    keys = path.split('.')
    current = config
    for key in keys:
        if key not in current:
            current[key] = {}
        current = current[key]


"""
Merge all input YAML files into a single dictionary, adding new values.
Overwrite existing subtrees if overwrite set to True.
"""
def deep_merge(base, new, overwrite=False):
    for key, value in new.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            deep_merge(base[key], value, overwrite=overwrite)
        else:
            if overwrite or key not in base:
                base[key] = value



def merge_inputs(input_files):
    merged_data = {}
    for input_file in input_files:
        with open(input_file, 'r') as infile:
            input_data = None
            try:
                # Try to parse as JSON
                input_data = json.load(infile)
            except json.JSONDecodeError:
                pass  # If not JSON, proceed to try YAML
            
            if not input_data:
                try:
                    # Reset file pointer and try to parse as YAML
                    infile.seek(0)
                    input_data = yaml.safe_load(infile)
                except yaml.YAMLError:
                    raise ValueError(f"File {input_file} is neither valid JSON nor YAML.")

            deep_merge(merged_data, input_data)
    return merged_data


# Get the PCI address of the SR-IOV device associated 
# with the given SR-IOV resource name in the sriov plugin configmap
def get_sriov_device_pci(sriov_resource_name):
    try:
        # Load kube config from the default service account (inside the pod)
        config.load_incluster_config()

        # Initialize the API client for CoreV1 (which handles ConfigMaps)
        v1 = client.CoreV1Api()

        # Retrieve the ConfigMap from the kube-system namespace
        config_map = v1.read_namespaced_config_map(name="sriov-device-plugin-config", namespace="kube-system")

        # Extract the 'config.json' string from the ConfigMap's data field
        config_json_str = config_map.data.get('config.json', '')

        # Convert the JSON string into a dictionary
        if config_json_str:
            config_dict = json.loads(config_json_str)
        else:
            print("config.json not found in the ConfigMap.")

        rname = sriov_resource_name.split('/')[-1]
        for sriov_resource in config_dict.get('resourceList', []):
            if sriov_resource.get('resourceName') == rname:
                return sriov_resource.get('selectors', {}).get('pciAddresses', [None])[0]

        print(f"SR-IOV resource '{sriov_resource_name}' not found.")
        return None

    except Exception as e:
        print(f"Error querying SR-IOV resources: {str(e)}")
        return None



# NOTE: For now we support only one DU and multiple RUs
# CU-DU split is not properly tested.
# Ref: https://docs.srsran.com/projects/project/en/latest/user_manuals/source/config_ref.html

def update_config(input_files, config_file, output_file, split, du_name):
    # Load the config YAML file
    with open(config_file, 'r') as confile:
        config_data = yaml.safe_load(confile)

    # Merge all input YAML files
    input_data = merge_inputs(input_files)
    logging.info(f"Configuring parameters: {json.dumps(input_data, indent=2)}\n")

    # Check if the du exists
    if du_name:
        du_config = input_data.get('duConfigs', {}).get(du_name)
        if not du_config:
            logging.error(f"DU {du_name} configs don't exist in the input files.")
            exit(1)
       

    ensure_path_exists(config_data, 'hal')
    if not config_data.get('hal').get('eal_args'):
        config_data['hal']['eal_args'] = ""


    # Update the destination config file
    if du_name:
        logging.info(f"Configuring (gNB with) DU {du_name}")
        # Update RU related values on two locations
        ensure_path_exists(config_data, 'ru_ofh')
        if 'cells' not in config_data['ru_ofh']:
            config_data['ru_ofh']['cells'] = []
        if 'cells' not in config_data:
            config_data['cells'] = []


        # cell_cfg, ru_ofh
        ensure_path_exists(config_data, 'cell_cfg')
        physicalCellID = list(du_config['cells'].values())[0].get('physicalCellID')
        ruDLArfcn = list(du_config['cells'].values())[0].get('ruDLArfcn')
        ruBandwidth = list(du_config['cells'].values())[0].get('ruBandwidth')
        if physicalCellID:
            config_data['cell_cfg']['pci'] = physicalCellID
        if ruDLArfcn:
            config_data['cell_cfg']['dl_arfcn'] = ruDLArfcn
        if ruBandwidth:
            config_data['cell_cfg']['channel_bandwidth_MHz'] = ruBandwidth
            config_data['ru_ofh']['ru_bandwidth_MHz'] = ruBandwidth

        if input_data.get('cell_cfg'):
            if not config_data.get('cell_cfg'):
                config_data['cell_cfg'] = copy.deepcopy(input_data.get('cell_cfg'))
            else:
                deep_merge(config_data['cell_cfg'], input_data.get('cell_cfg'), overwrite=True)



        # ru_ofh/cells
        for ind, ru in enumerate(du_config['cells'].values()):
            if ind >= len(config_data['ru_ofh']['cells']):
                # If RU doesn't exist in the config, add a new one
                # and copy the default values from the last RU
                if len(config_data['ru_ofh']['cells']) > 0:
                    config_data['ru_ofh']['cells'].append(copy.deepcopy(config_data['ru_ofh']['cells'][-1]))
                else:
                    config_data['ru_ofh']['cells'].append({})
            if ru.get("ruLocalMAC"):
                config_data['ru_ofh']['cells'][ind]['du_mac_addr'] = ru["ruLocalMAC"]
            if ru.get("ruRemoteMAC"):
                config_data['ru_ofh']['cells'][ind]['ru_mac_addr'] = ru["ruRemoteMAC"]
            if ru.get("ruVLAN"):
                config_data['ru_ofh']['cells'][ind]['vlan_tag_cp'] = int(ru["ruVLAN"])
                config_data['ru_ofh']['cells'][ind]['vlan_tag_up'] = int(ru["ruVLAN"])
            if ru.get("prachPortID"):
                config_data['ru_ofh']['cells'][ind]['prach_port_id'] = ru["prachPortID"]
            if ru.get("dlPortID"):
                config_data['ru_ofh']['cells'][ind]['dl_port_id'] = ru["dlPortID"]
            if ru.get("ulPortID"):
                config_data['ru_ofh']['cells'][ind]['ul_port_id'] = ru["ulPortID"]
            ruBandwidth = list(du_config['cells'].values())[ind].get('ruBandwidth')                


            pcie_addr = get_sriov_device_pci(ru.get("ruDPDKResource"))
            if not pcie_addr:
                logging.error(f"PCI address not found for SR-IOV resource {ru.get('ruDPDKResource')} in the config file. Exiting.")
                exit(1)

            config_data['ru_ofh']['cells'][ind]['network_interface'] = pcie_addr
            config_data['hal']['eal_args'] += f" -a {pcie_addr}"

            if ind >= len(config_data['cells']):
                # If RU doesn't exist in the config, add a new one
                # and copy the default values from the last RU
                if len(config_data['cells']) > 0:
                    config_data['cells'].append(copy.deepcopy(config_data['cells'][-1]))
                else:
                    config_data['cells'].append({})
            if ru.get("physicalCellID"):
                config_data['cells'][ind]['pci'] = ru["physicalCellID"]
            if ru.get("ruDLArfcn"):
                config_data['cells'][ind]['dl_arfcn'] = ru["ruDLArfcn"]
            if ru.get("prachPortID"):
                config_data['ru_ofh']['cells'][ind]['prach_port_id'] = ru["prachPortID"]
            if ru.get("dlPortID"):
                config_data['ru_ofh']['cells'][ind]['dl_port_id'] = ru["dlPortID"]
            if ru.get("ulPortID"):
                config_data['ru_ofh']['cells'][ind]['ul_port_id'] = ru["ulPortID"]
    else:
        logging.info(f"Configuring CU {du_name}")



    if input_data.get('cu_cp'):
        if not config_data.get('cu_cp'):
            config_data['cu_cp'] = copy.deepcopy(input_data.get('cu_cp'))
        else:
            deep_merge(config_data['cu_cp'], input_data.get('cu_cp'), overwrite=True)
    # Extract the core IP
    # This must come after the previous 'cu_cp' config as the coreIP is specified in a second 'values' file
    core_ip = input_data['ngcParams']['coreIP']
    ensure_path_exists(config_data, 'cu_cp.amf')
    config_data['cu_cp']['amf']['addr'] = core_ip

    # Extract local CUUP IP address to announce to the AMF
    sriov = input_data['sriov']
    cuup_ip = sriov['cuup_ip']
    ensure_path_exists(config_data, 'cu_up.ngu.socket')
    cuup_sock = {
        "bind_addr": cuup_ip
    }
    config_data['cu_up']['ngu']['socket'] = []
    config_data['cu_up']['ngu']['socket'].append(cuup_sock)

    # NOTE: not tested
    if split:
        cucp_ip = sriov.get('cucp_ip')
        if not du_name:
            ensure_path_exists(config_data, 'cu_f1ap')
            if cucp_ip:
                config_data['cu_f1ap']['bind_addr'] = cucp_ip
        else:
            ensure_path_exists(config_data, 'f1ap')
            if cucp_ip:
                config_data['f1ap']['cu_cp_addr'] = cucp_ip
            # Not sure if we need this one:
            #config_data['f1ap']['bind_addr'] = TBD
            # It seems srs uses one IP and we don't need cuup_ip



    # If defined, pass-thru unmodified srsRAN config params
    # (and in process delete any original config)
    if input_data.get('metrics'):
        if not config_data.get('metrics'):
            config_data['metrics'] = copy.deepcopy(input_data.get('metrics'))
        else:
            deep_merge(config_data['metrics'], input_data.get('metrics'), overwrite=True)
    if input_data.get('pcap'):
        if not config_data.get('pcap'):
            config_data['pcap'] = copy.deepcopy(input_data.get('pcap'))
        else:
            deep_merge(config_data['pcap'], input_data.get('pcap'), overwrite=True)
    if input_data.get('log'):
        if not config_data.get('log'):
            config_data['log'] = copy.deepcopy(input_data.get('log'))
        else:
            deep_merge(config_data['log'], input_data.get('log'), overwrite=True)


    if input_data.get('system', {}).get('eal_cpu_args'):
        config_data['hal']['eal_args'] = input_data['system']['eal_cpu_args'] + " " + config_data['hal']['eal_args']

    if input_data.get('system', {}).get('taskset_cpu_args'):
        # Write to a shell script
        with open("def_taskset.sh", "w") as script_file:
            script_file.write(f"export TASKSET_CPU_ARGS='{input_data['system']['taskset_cpu_args']}'\n")

    if input_data.get('jbpf'):
        if input_data.get('jbpf').get('enabled', True):
            if input_data.get('jbpf').get('cfg'):
                if not config_data.get('jbpf'):
                    config_data['jbpf'] = copy.deepcopy(input_data.get('jbpf').get('cfg'))
                else:
                    deep_merge(config_data['jbpf'], input_data.get('jbpf').get('cfg'), overwrite=True)

    # Write the updated config to the output file
    with open(output_file, 'w') as outfile:
        yaml.dump(config_data, outfile, default_flow_style=False)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an srsRAN config file based of an initial srsRAN config file (msft_config.yaml) "
                                     "and one or more additional testbed config file (in a different yaml format). "
                                     "This can be done for a DU/gNB (in which case you need to specify the DU name) "
                                     "or for a CU (in which case you don't provide the du_name parameter)."
                                     )
    parser.add_argument("--inputs", nargs='+', required=True, help="List of input YAML files.")
    parser.add_argument("--config", required=True, help="Path to the config YAML file.")
    parser.add_argument("--output", required=True, help="Path to the output YAML file.")
    parser.add_argument("--split", action='store_true', help="Set to configure split DU/CU. Default is monolithic gNB.")
    parser.add_argument("--du_name", 
                        help="Name of the DU to be configured "
                        "(matching the input YAML file, typically du1). " 
                        "If omitted, we configure CU.")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    update_config(args.inputs, args.config, args.output, args.split, args.du_name)
    logging.info(f"Updated configuration written to {args.output}")