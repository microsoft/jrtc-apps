#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

CACHE_FLAG=
GCC_ARCH=x86-64-v3

CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source $(dirname $(dirname "$CURRENT_DIR"))/set_vars.sh

Usage()
{
   # Display Help
   echo "Build srsRan image"
   echo "options:"
   echo "[-s]    Optional image tag.  Default='$SRSRAN_IMAGE_TAG'"
   echo "[-m]    Optional CPU march target.  Default='x86-64-v3' (AVX2)"
   echo "[-c]    Optional.  If included, '--no-cache- is added to the Docker build"
   echo
}

# Get the options
while getopts "s:m:c" option; do
	case $option in
		s) # Set image tag
			SRSRAN_IMAGE_TAG="$OPTARG";;
		m) # Set CPU march target
			GCC_ARCH="$OPTARG";;
		c) # Set image tag
			CACHE_FLAG="--no-cache";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Usage
			exit 1;;
	esac
done

echo SRSRAN_IMAGE_TAG $SRSRAN_IMAGE_TAG
echo GCC_ARCH $GCC_ARCH

docker build $CACHE_FLAG \
    --build-arg SRSRAN_IMAGE_TAG=${SRSRAN_IMAGE_TAG} \
    --build-arg GCC_ARCH=${GCC_ARCH} \
    -t ghcr.io/microsoft/jrtc-apps/srs-ue:${SRSRAN_IMAGE_TAG} -f SRS-ue.Dockerfile .


exit 0
