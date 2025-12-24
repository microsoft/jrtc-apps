import copy
import json
import logging
import yaml
import argparse
from pprint import pprint
from kubernetes import client, config

from update_config import ensure_path_exists, deep_merge, merge_inputs, update_cucp, update_cuup, \
    update_generic, update_jbpf, write_taskset_script


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

    if input_data.get('cell_cfg'):
        if not config_data.get('cell_cfg'):
            config_data['cell_cfg'] = copy.deepcopy(input_data.get('cell_cfg'))
        else:
            deep_merge(config_data['cell_cfg'], input_data.get('cell_cfg'), overwrite=True)

    # zmp cell params
    physicalCellID = input_data.get('zmq', {}).get('cell', {}).get('physicalCellID', None)
    if physicalCellID is not None:
        config_data['cell_cfg']['pci'] = physicalCellID
        config_data['cells'][0]['pci'] = physicalCellID

    update_cucp(input_data, config_data)

    update_cuup(input_data, config_data)

    # If defined, pass-thru unmodified srsRAN config params
    # (and in process delete any original config)
    update_generic(input_data, config_data, 'metrics')
    update_generic(input_data, config_data, 'pcap')
    update_generic(input_data, config_data, 'log')

    update_jbpf(input_data, config_data)

    write_taskset_script(input_data, config_data, "def_taskset.sh")

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