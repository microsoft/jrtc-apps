
#!/bin/bash
set -euo pipefail

#######################################
# Globals & init
#######################################

CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source "$(dirname "$(dirname "$CURRENT_DIR")")/set_vars.sh"
source "$CURRENT_DIR/helpers.sh"



#######################################
zmq_clear_triggers() {

    jq -e '.zmq != null' <<<"$ALL_VALUES" >/dev/null \
        || fatal "ZMQ section is missing or null in ALL_VALUES"

    zmq=$(jq '.zmq' <<<"$ALL_VALUES")

    if ! jq -e '.enabled == true' <<<"$zmq" >/dev/null; then
        # echo "⚠ ZMQ is disabled in Helm values, skipping triggers"
        return
    fi

    zmq_host_path=$(jq_required "$zmq" '.triggerFiles.hostPath')
    zmq_start_grc_file=$(jq_required "$zmq" '.triggerFiles.startGRC')
    zmq_start_connections_file=$(jq_required "$zmq" '.triggerFiles.startConnections')
    zmq_start_traffic_file=$(jq_required "$zmq" '.triggerFiles.startTraffic')

    for f in "$zmq_start_connections_file" "$zmq_start_traffic_file"; do
        if [ -z "$f" ]; then
            # "Skipping empty trigger file entry."
            continue
        fi

        full_path="$zmq_host_path/$f"
        if [ -f "$full_path" ]; then
            echo "Removing trigger file: $full_path"
            sudo rm -f "$full_path"
        fi
    done
}

#######################################
zmq_wait_grc() {
    echo -e "\nWaiting for GRC complete its initialisation"

    local namespace="ran"
    local podname=$(kubectl -n "$namespace" get pods -l app=srs-grc-du1 -o jsonpath='{.items[*].metadata.name}')
    local container="grc"
    local pattern="Starting flowgraph"
    local timeout=60    # seconds
    local interval=1    # seconds between checks
    local elapsed=0

    while [ $elapsed -lt $timeout ]; do

        if kubectl -n "$namespace" logs "$podname" -c "$container" --tail=20 2>/dev/null | grep -q "$pattern"; then
            sleep 5   # give GRC a few second to complete init
            echo -e " ✅ GRC initialisation completed\n"
            return
        fi

        # Print a dot for each iteration
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    fatal "Timeout waiting for GRC to complete its initialisation after ${timeout}s"
}

#######################################
zmq_trigger_and_wait_grc() {
    echo -e "\nTriggering ZMQ GRC container"
    sudo mkdir -p "$zmq_host_path"
    sudo touch "$zmq_host_path/$zmq_start_grc_file"
    zmq_wait_grc
}

#######################################
zmq_wait_ue_connection() {
    local i=$1
    local podname=$2
    local namespace="ran"
    local container="ue"
    local pattern="PDU Session Establishment successful"
    local timeout=60    # seconds
    local interval=1    # seconds between checks
    local elapsed=0

    echo -e "\nWaiting for UE-$i to complete PDU Session Establishment"
    while [ $elapsed -lt $timeout ]; do

        if kubectl -n "$namespace" logs "$podname" -c "$container" --tail=20 2>/dev/null | grep -q "$pattern"; then
            echo -e " ✅ UE-$i successfully completed PDU Session Establishment\n"
            return
        fi

        # Print a dot for each iteration
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    fatal "Timeout waiting for UE-$i to complete a PDU Session Establishment after ${timeout}s"
}

#######################################
zmq_wait_ue_connections() {
    # Get all UE pod names into an array
    UE_PODS=($(kubectl -n ran get pods -l app.kubernetes.io/component=ue -o jsonpath='{.items[*].metadata.name}'))
    if [ "${#UE_PODS[@]}" -eq 0 ]; then
        fatal "No UE pods found (label app.kubernetes.io/component=ue)"
    fi

    # Loop through each UE pod
    i=1
    for podname in "${UE_PODS[@]}"; do
        zmq_wait_ue_connection $i $podname
        i=$((i + 1))  # increment counter
    done
}

#######################################
zmq_trigger_and_wait_ue_connections() {
    echo -e "\nTriggering ZMQ UE containers"
    sudo mkdir -p "$zmq_host_path"
    sudo touch "$zmq_host_path/$zmq_start_connections_file"
    zmq_wait_ue_connections 
}

#######################################
zmq_trigger_traffic() {
    echo -e "\nTriggering ZMQ traffic containers"
    sudo mkdir -p "$zmq_host_path"
    sudo touch "$zmq_host_path/$zmq_start_traffic_file"
}


#######################################
# Main
#######################################

zmq_trigger_procedures() {
    zmq_trigger_and_wait_grc
    zmq_trigger_and_wait_ue_connections
    zmq_trigger_traffic
}

