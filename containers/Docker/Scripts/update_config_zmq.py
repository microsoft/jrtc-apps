import copy
import json
import logging
import yaml
import argparse
from pprint import pprint
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

def update_config(input_files, config_file, output_file, split):
    # Load the config YAML file
    with open(config_file, 'r') as confile:
        config_data = yaml.safe_load(confile)

    # Merge all input YAML files
    input_data = merge_inputs(input_files)

    ensure_path_exists(config_data, 'cell_cfg')
    # zmp cell params
    physicalCellID = input_data.get('zmq', {}).get('physicalCellID', None)
    if physicalCellID is not None:
        config_data['cell_cfg']['pci'] = physicalCellID

    # cell_cfg.slicing
    slicing = input_data.get('cell_cfg', {}).get('slicing', None)
    if slicing is not None:
        config_data['cell_cfg']['slicing'] = slicing

    # cell_cfg.tdd_ul_dl_cfg
    tdd_ul_dl_cfg = input_data.get('cell_cfg', {}).get('tdd_ul_dl_cfg', None)
    if tdd_ul_dl_cfg is not None:
        config_data['cell_cfg']['tdd_ul_dl_cfg'] = tdd_ul_dl_cfg

    # Extract the core IP
    # This must come after the previous 'cu_cp' config as the coreIP is specified in a second 'values' file
    core_ip = input_data['ngcParams']['coreIP']
    ensure_path_exists(config_data, 'cu_cp.amf')
    config_data['cu_cp']['amf']['addr'] = core_ip

   
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
                                     )
    parser.add_argument("--inputs", nargs='+', required=True, help="List of input YAML files.")
    parser.add_argument("--config", required=True, help="Path to the config YAML file.")
    parser.add_argument("--output", required=True, help="Path to the output YAML file.")
    parser.add_argument("--split", action='store_true', help="Set to configure split DU/CU. Default is monolithic gNB.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    update_config(args.inputs, args.config, args.output, args.split)
    logging.info(f"Updated configuration written to {args.output}")