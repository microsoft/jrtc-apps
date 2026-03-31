#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source $(dirname $(dirname "$CURRENT_DIR"))/set_vars.sh

MARCH=x86-64-v3

Usage()
{
   # Display Help
   echo "Build srsRan=Jbpf zmq image"
   echo "options:"
   echo "[-s]    Optional srsRan image tag.  Default='$SRSRAN_IMAGE_TAG'"
   echo "[-m]    Optional CPU march target.  Default='x86-64-v3' (AVX2)"
   echo
}

# Get the options
#while getopts "b:s:c" option; do
while getopts "s:m:c" option; do
	case $option in

		s) # Set image tag
			SRSRAN_IMAGE_TAG="$OPTARG";;
		m) # Set CPU march target
			MARCH="$OPTARG";;
		c) # Set image tag
			CACHE_FLAG="--no-cache";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Usage
			exit 1;;
	esac
done

#echo BASE_IMAGE_TAG $BASE_IMAGE_TAG
echo SRSRAN_IMAGE_TAG $SRSRAN_IMAGE_TAG
echo MARCH $MARCH

docker build $CACHE_FLAG \
    --build-arg SRS_JBPF_IMAGE_TAG=${SRSRAN_IMAGE_TAG} \
    --build-arg MARCH=${MARCH} \
    -t ghcr.io/microsoft/jrtc-apps/srs-jbpf-zmq:${SRSRAN_IMAGE_TAG} -f SRS-jbpf-zmq.Dockerfile .


exit 0
