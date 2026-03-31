#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

MARCH=x86-64-v3
CACHE_FLAG=

CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source $(dirname $(dirname "$CURRENT_DIR"))/set_vars.sh

BASE_IMAGE_TAG=$SRSRAN_IMAGE_TAG

Usage()
{
   # Display Help
   echo "Build srsRan image"
   echo "options:"
   echo "[-b]    Optional base image tag.  Default='$SRSRAN_IMAGE_TAG'"
   echo "[-s]    Optional image tag.  Default='$SRSRAN_IMAGE_TAG'"
   echo "[-m]    Optional CPU march target.  Default='x86-64-v3' (AVX2)"
   echo "[-c]    Optional.  If included, '--no-cache- is added to the Docker build"
   echo
}

# Get the options
while getopts "b:s:m:c" option; do
	case $option in
		b) # Set image tag
			BASE_IMAGE_TAG="$OPTARG";;
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

echo BASE_IMAGE_TAG $BASE_IMAGE_TAG
echo SRSRAN_IMAGE_TAG $SRSRAN_IMAGE_TAG
echo MARCH $MARCH

# Apply jbpf 3p patches (ck, mimalloc, ebpf-verifier) since INITIALIZE_SUBMODULES=OFF
# skips init_and_patch_submodules.sh which requires git inside the container.
JBPF_DIR=srsRAN_Project/external/jbpf
if [ -f "$JBPF_DIR/patches/ck.patch" ]; then
    echo "Applying jbpf 3p patches..."
    cd "$JBPF_DIR/3p/ck" && patch -p1 --forward -r- < ../../patches/ck.patch || true
    cd "$CURRENT_DIR"
    cd "$JBPF_DIR/3p/mimalloc" && patch -p1 --forward -r- < ../../patches/mimalloc.patch || true
    cd "$CURRENT_DIR"
    cd "$JBPF_DIR/3p/ebpf-verifier" && patch -p1 --forward -r- < ../../patches/ebpf_verifier.patch || true
    cd "$CURRENT_DIR"
fi

docker build $CACHE_FLAG \
    --build-arg BASE_IMAGE_TAG=${BASE_IMAGE_TAG} \
    --build-arg MARCH=${MARCH} \
    -t ghcr.io/microsoft/jrtc-apps/srs-jbpf:${SRSRAN_IMAGE_TAG} -f SRS-jbpf.Dockerfile .

exit 0
