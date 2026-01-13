#!/bin/bash

# Create the final config file
python3 update_config.py --config /du-config/default_config.yaml --output config.yaml --input /du-config/config.json --du_name $(jq -r '.duConfigs | keys[0]' /du-config/config.json)


# Source def_taskset.sh if it exists
if [[ -f "def_taskset.sh" ]]; then
    echo "Sourcing def_taskset.sh..."
    source def_taskset.sh
else
    echo "def_taskset.sh not found. Skipping..."
fi

# Check if TASKSET_CPU_ARGS is defined
if [[ -n "$TASKSET_CPU_ARGS" ]]; then
    # Run the command with taskset
    echo "Running with taskset: taskset -c $TASKSET_CPU_ARGS gnb -c config.yaml"
    taskset -c "$TASKSET_CPU_ARGS" gnb -c config.yaml
else
    # Run the command without taskset
    echo "Running without taskset: gnb -c config.yaml"
    gnb -c config.yaml
fi
