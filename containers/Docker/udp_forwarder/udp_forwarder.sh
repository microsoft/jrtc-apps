#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

required_env_vars="LISTEN_IP LISTEN_PORT FORWARD_IP FORWARD_PORT"
for env_var in $required_env_vars; do
    if [[ -z ${!env_var} ]]; then
        echo "ERROR:  $env_var is undefined !! "
        return
    fi
done

python3 /udp_forwarder/udp_forwarder.py --listen-ip $LISTEN_IP --listen-port $LISTEN_PORT --forward-ip $FORWARD_IP --forward-port $FORWARD_PORT