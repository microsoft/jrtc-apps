#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

IMAGE_TAG=latest

Usage()
{
   # Display Help
   echo "Build GNU Radio Companion image"
   echo "options:"
   echo "[-b]    Optional base image tag.  Default='latest'"
   echo
}

# Get the options
while getopts "b:" option; do
	case $option in
		b) # Set image tag
			IMAGE_TAG="$OPTARG";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Usage
			exit 1;;
	esac
done

echo IMAGE_TAG $IMAGE_TAG

docker build -t ghcr.io/microsoft/jrtc-apps/grc:$IMAGE_TAG -f GRC.Dockerfile .

exit 0
