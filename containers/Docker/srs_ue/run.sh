#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

required_env_vars="TX_PORT RX_ADDR RX_PORT IMSI IMEI APN"
for env_var in $required_env_vars; do
    if [[ -z ${!env_var} ]]; then
        echo "ERROR:  $env_var is undefined !! "
        exit 1
    fi
done

echo TX_PORT $TX_PORT
echo RX_ADDR $RX_ADDR
echo RX_PORT $RX_PORT
echo IMSI $IMSI
echo IMEI $IMEI
echo APN $APN

echo "Replacing ENV vars .."
envsubst < ue_zmq.conf.template > ue_zmq.conf 

echo -e "\nGenerated ue_zmq.conf:\n"
cat ue_zmq.conf

echo -e "\nStarting UE ...\n"
srsue ue_zmq.conf
