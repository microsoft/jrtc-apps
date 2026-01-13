#!/bin/bash

# Substiture ZMQ env vars
envsubst < msft_config_zmq.yaml > msft_config.yaml

# Create the final config file
python3 update_config_zmq.py --config msft_config.yaml --output config.yaml --input /du-config/config.json 

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
