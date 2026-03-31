#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source $(dirname $(dirname "$CURRENT_DIR"))/set_vars.sh

BASE_IMAGE_TAG=$SRSRAN_IMAGE_TAG

Usage()
{
   # Display Help
   echo "Build srsRan base image"
   echo "options:"
   echo "[-b]    Optional base image tag.  Default='$SRSRAN_IMAGE_TAG'"
   echo
}

# Get the options
while getopts "b:" option; do
	case $option in
		b) # Set image tag
			BASE_IMAGE_TAG="$OPTARG";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Usage
			exit 1;;
	esac
done

echo BASE_IMAGE_TAG $BASE_IMAGE_TAG

docker build -t ghcr.io/microsoft/jrtc-apps/base/srs:$BASE_IMAGE_TAG -f base.Dockerfile .

exit 0
