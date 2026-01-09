#!/bin/bash
set -euo pipefail

#######################################
# Globals & init
#######################################

CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source "$(dirname "$(dirname "$CURRENT_DIR")")/set_vars.sh"
source "$CURRENT_DIR/zmq_helpers.sh"
source "$CURRENT_DIR/helpers.sh"

#######################################
# Helpers
#######################################

print_image_tag() {
    local field="$1"
    local values="$2"

    local image_tag
    image_tag=$(echo "$values" | jq -r ".image.$field" | awk -F ':' '{print $NF}')

    if [ -n "$image_tag" ]; then
        echo "    Image tag for $field: $image_tag"
    fi
}

Help() {
    echo "Install RAN."
    echo
    echo "Syntax: install [-h <local_chart_path>|-f <values_file>|-v <image_tag>]"
    echo "options:"
    echo "-?     Show this help message"
    echo "-f     (Optional) Extra values config file"
    echo "-v     (Optional) Helm chart version ($CHART_VERSION is the default)"
    echo "-h     (Optional) Install Helm from a local path"
    echo "-b     (Optional) Local path with compiled jbpf codelets"
    echo "-c     (Optional) CodeletSets to load automatically. "
    echo "-d     (Optional) Debug mode"
    echo
}

#######################################
# Argument parsing
#######################################

parse_args() {
    CHART_VERSION="0.2"
    VALUES_FILES=""
    VERSION="$CHART_VERSION"
    LOCAL_PATH=""
    CODELET_SETS=()
    DEBUG=""

    while getopts "n:f:v:h:c:db" option; do
        case $option in
            f) VALUES_FILES="$VALUES_FILES $OPTARG" ;;
            v) VERSION="$OPTARG" ;;
            h) LOCAL_PATH="$OPTARG" ;;
            b) JBPF_CODELETS="$OPTARG" ;;
            c) CODELET_SETS+=("$OPTARG") ;;
            d) DEBUG="DEBUG" ;;
            \?) Help; exit 1 ;;
        esac
    done
}

#######################################
# Helm source
#######################################

resolve_helm_source() {
    if [[ -z "${LOCAL_PATH}" ]]; then
        HELM_URL="oci://ghcr.io/microsoft/jrtc-apps/helm/srs-ran-5g-jbpf --version ${VERSION}"
    else
        HELM_URL="${LOCAL_PATH}"
        echo "Using Helm from local path: ${LOCAL_PATH}"
    fi
}

#######################################
# Values files
#######################################

process_values_files() {
    EXTRA_VALUES=""
    EXTRA_VALUES_SUMMARY=""

    for values_file in $VALUES_FILES; do
        [ -f "$values_file" ] || fatal "Values file does not exist: $values_file"
        EXTRA_VALUES+=" -f $values_file"
        EXTRA_VALUES_SUMMARY+=" $values_file"
    done

    echo "Extra values files:${EXTRA_VALUES_SUMMARY}"
}

#######################################
# Log Analytics
#######################################

setup_log_analytics() {
    LA_OPTIONS=""

    if [[ -n "${LA_WORKSPACE_ID:-}" && -n "${LA_PRIMARY_KEY:-}" ]]; then
        LA_OPTIONS="\
        --set jrtc_controller.log_analytics.enabled=true \
        --set jrtc_controller.log_analytics.workspace_id=$LA_WORKSPACE_ID \
        --set jrtc_controller.log_analytics.primary_key=$LA_PRIMARY_KEY \
        --set jrtc_controller.local_decoder.log_analytics.enabled=true"
        echo "Using Log Analytics workspace ID: $LA_WORKSPACE_ID"
    else
        echo "No Log Analytics workspace ID or API key provided. Skipping."
    fi
}

#######################################
# Debug
#######################################

setup_debug() {
    DEBUG_OPTIONS=""
    if [ -n "$DEBUG" ]; then
        DEBUG_OPTIONS="--set debug_mode.enabled=true"
    fi
}

#######################################
# JBPF / JRTC
#######################################

setup_codelets() {
    if [ -z "${JBPF_CODELETS:-}" ]; then
        JBPF_CODELETS=$(realpath "${CURRENT_DIR}/../../codelets/")
    fi
    JBPF_OPTIONS="--set-string jbpf.codelets_vol_mount=$JBPF_CODELETS"
    echo "Codelet mount point: ${JBPF_CODELETS}"
}

setup_jrtc() {
    if [ "${USE_JRTC}" -eq 1 ]; then
        if [ -z "${JBPF_APPS:-}" ]; then
            JBPF_APPS=$(realpath "${CURRENT_DIR}/../../jrtc_apps/")
        fi
        JRTC_OPTIONS="\
        --set-string jrtc_controller.apps_vol_mount=$JBPF_APPS \
        --set-string HOSTNAME=$(hostname)"
        echo "App mount point: ${JBPF_APPS}"
    else
        JRTC_OPTIONS=""
    fi
}

#######################################
# Images
#######################################

setup_images() {
    SRSRAN_IMAGES="\
    --set-string image.srs_jbpf=ghcr.io/microsoft/jrtc-apps/srs-jbpf:$SRSRAN_IMAGE_TAG \
    --set-string image.srs_jbpf_proxy=ghcr.io/microsoft/jrtc-apps/srs-jbpf-sdk:$SRSRAN_IMAGE_TAG \
    --set-string image.srs_jbpf_zmq=ghcr.io/microsoft/jrtc-apps/srs-jbpf-zmq:$SRSRAN_IMAGE_TAG \
    --set-string image.srs_ue=ghcr.io/microsoft/jrtc-apps/srs-ue:$SRSRAN_IMAGE_TAG"
}

#######################################
# Install & summary
#######################################

create_namespace() {
    kubectl create namespace ran || true
}

install_chart() {
    helm install \
        $EXTRA_VALUES \
        $DEBUG_OPTIONS \
        $JBPF_OPTIONS \
        $LA_OPTIONS \
        $JRTC_OPTIONS \
        $SRSRAN_IMAGES \
        -n ran ran $HELM_URL
}

get_values() {
    CUSTOM_VALUES=$(helm -n ran get values ran --output json)
    ALL_VALUES=$(helm -n ran get values ran --all --output json)
}

print_summary() {
    echo
    echo "*** Custom Helm chart configs:"
    echo

    echo "Custom image tags (if any):"
    print_image_tag "srs" "$CUSTOM_VALUES"

    debug_mode_enabled=$(jq_required "$ALL_VALUES" '.debug_mode.enabled')
    echo -e "\nDEBUG Mode: $debug_mode_enabled"

    jrtc_enabled=$(jq_required "$ALL_VALUES" '.jbpf.cfg.jbpf_enable_ipc')
    echo -e "\nJRTC enabled: $jrtc_enabled"    

    zmq_enabled=$(jq_required "$ALL_VALUES" '.zmq.enabled')
    echo -e "\nZMQ enabled: $zmq_enabled"    

    if [ ! "$zmq_enabled" == "true" ]; then
        echo "Custom cell config (if any):"
        echo "$ALL_VALUES" | jq -r '
            .duConfigs | keys[] as $du |
            "\($du): \(.[$du].cells | to_entries[] | select(.value.perf != null) |
            "  Cell: \(.key)\n    Perf structure: \(.value.perf | tojson)")"'
        echo
    fi

    echo "Janus out IP: \
$(echo "$ALL_VALUES" | jq -r '.debug_mode.janus.out_ip'):\
$(echo "$ALL_VALUES" | jq -r '.debug_mode.janus.out_port')"
}


#######################################
# Wait for pods
#######################################

wait_pod_ready() {
    local namespace=$1
    local podname=$2
    local timeout=$3
    echo -e "\nWaiting for "$podname" to be in Ready state"
    kubectl wait \
        -n "$namespace" \
        --for=condition=Ready \
        pod/"$podname" \
        --timeout="$timeout" \
    || fatal "Pod $podname in namespace $namespace did not become Ready within $timeout"

    echo "$podname is now in Ready state"
}

wait_jrtc_ready() {
    if [ "$jrtc_enabled" == "1" ]; then
        local namespace="ran"
        local podname=$(kubectl -n "$namespace" get pods -l app=jrtc-service -o jsonpath='{.items[*].metadata.name}')
        wait_pod_ready "$namespace" "$podname" 5m
    fi
}

wait_gnb_ready() {
    local namespace="ran"
    local podname=$(kubectl -n "$namespace" get pods -l app=srs-gnb-du1 -o jsonpath='{.items[*].metadata.name}')
    wait_pod_ready "$namespace" "$podname" 5m
}

wait_gnb_amf_connected() {
    local namespace="ran"
    local podname=$(kubectl -n "$namespace" get pods -l app=srs-gnb-du1 -o jsonpath='{.items[*].metadata.name}')
    local container="gnb"
    local pattern="N2: Connection to AMF"
    local timeout=60    # seconds
    local interval=1    # seconds between checks
    local elapsed=0

    echo -e "\nWaiting for gNB to connect to AMF"
    while [ $elapsed -lt $timeout ]; do

        if kubectl -n "$namespace" logs "$podname" -c "$container" --tail=20 2>/dev/null | grep -q "$pattern"; then
            echo -e " ✅ gNB successfully connected to AMF\n"
            return
        fi

        # Print a dot for each iteration
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    fatal "Timeout waiting for gNB to connect to AMF after ${timeout}s"
}


#######################################
# Load jrtc/jbpf codelets
#######################################

autoload_codeletSets() {
    # load the codeletSets
    JRTC_APPS_DIR=$CURRENT_DIR/../../jrtc_apps
    for c in "${CODELET_SETS[@]}"; do
        pushd .
        cd $JRTC_APPS_DIR
        echo "Loading $c"
        ./load.sh -y "$c" 
        status=$?           # capture exit status
        popd > /dev/null    # return to original dir
        if [ $status -ne 0 ]; then
            fatal "Failure when loading $c"
        fi        
    done
}



#######################################
# Main
#######################################

main() {
    parse_args "$@"
    echo CHART_VERSION $CHART_VERSION
    resolve_helm_source
    process_values_files
    setup_log_analytics
    setup_debug
    setup_codelets
    setup_jrtc
    setup_images
    create_namespace
    install_chart
    get_values
    print_summary
    zmq_clear_triggers
    [ "$debug_mode_enabled" == "true" ] && return
    wait_jrtc_ready
    wait_gnb_ready
    wait_gnb_amf_connected
    autoload_codeletSets
    [ "$zmq_enabled" == "true" ] && zmq_trigger_procedures
}

main "$@"

exit 0
