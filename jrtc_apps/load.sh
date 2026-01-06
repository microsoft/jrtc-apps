#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

SDK_IMAGE_TAG=latest
CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source $CURRENT_DIR/../set_vars.sh

Help()
{
   # Display Help
   echo "Load JRTC app."
   echo
   echo "Syntax: $0 -y <deployment-yaml>"
   echo "options:"
   echo "[-s]   Optional SDK image tag.  Default='latest'"
   echo "-y     App yaml file with path"
   echo
}

DEPLOYMENT_YAML=""

# Get the options
while getopts "s:y:" option; do
	case $option in
		s) # Set image tag
			SDK_IMAGE_TAG="$OPTARG";;
		y) 
			DEPLOYMENT_YAML="$OPTARG";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Help
			exit 1;;
	esac
done

echo SDK_IMAGE_TAG $SDK_IMAGE_TAG

if [[ -z "$DEPLOYMENT_YAML" || ! -f "$DEPLOYMENT_YAML" ]]; then
    echo "Error: DEPLOYMENT_YAML is either not set or the file does not exist."
    Help
    exit 1
fi

DEPLOYMENT_YAML_FILENAME=$(basename "$DEPLOYMENT_YAML")
DEPLOYMENT_YAML_PATH=$(dirname "$DEPLOYMENT_YAML")

if [ "$SRS_JBPF_DOCKER" -eq 1 ]; then
    $DOCKER_CMD run --network=host \
        -v $CURRENT_DIR:/apps \
        -v $CURRENT_DIR/../codelets:/codelets \
        -e "JRTC_APPS=/apps" \
        -e "JBPF_CODELETS=/codelets" \
        -e "JRTC_PATH=/jrtc" \
        --entrypoint /jrtc/out/bin/jrtc-ctl \
        ghcr.io/microsoft/jrt-controller/jrt-controller-azurelinux:$SDK_IMAGE_TAG \
        load -c /apps/$DEPLOYMENT_YAML --log-level trace
    ret=$?
else
    pushd . > /dev/null
    cd $DEPLOYMENT_YAML_PATH
    if [[ -z "$JRTC_CTL_BIN" || ! -f "$JRTC_CTL_BIN" ]]; then
        echo "Error: JRTC_CTL_BIN is either not set or the file does not exist."
        Help
        exit 1
    fi

    $JRTC_CTL_BIN load -c $DEPLOYMENT_YAML_FILENAME --log-level trace
    ret=$?
    popd > /dev/null
fi

exit $ret
