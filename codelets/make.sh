#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

CURRENT_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
source $(dirname $CURRENT_DIR)/set_vars.sh
SDK_IMAGE_TAG=$SRSRAN_IMAGE_TAG

Help()
{
   # Display Help
   echo "Make janus codelets ."
   echo
   echo "Syntax: make [-d <directory>|-i <image_tag>|-o <extra_option>]"
   echo "options:"
   echo "[-d]   Run make in <directory> subfolder."
   echo "[-i]   <image-tag>."
   echo "-o     Add extra options to make (can be repeated multiple times)."
   echo
}

OPTIONS=""
USE_DIRECTORY_FLAG=false

# Get the options
while getopts "t:d:i:o:" option; do
	case $option in
		i) # Set image tag
            SDK_IMAGE_TAG="$OPTARG";;
		d) # Run make in a specific directory
			USE_DIRECTORY_FLAG=true
			USE_DIRECTORY=$OPTARG;;
		o) # Extra option to add to Makefile
			OPTIONS="$OPTIONS $OPTARG";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Help
			exit;;
	esac
done

# Not sure what is the best way to check that
# the parameters passed start with a dash.
# So adding a simple hack that checks that
# the first parameter has a dash.
if [ ! -z "$1" ] && [ $OPTIND == "1" ]; then
	echo "Error: Invalid option"
	Help
	exit 1
fi
 
# Create list of codelet folders to build
codelet_folder_list=()
if [ "$USE_DIRECTORY_FLAG" = true ]; then
	codelet_folder_list+=("$USE_DIRECTORY")
else
	for lib in */; do
			[ -d "$lib" ] && codelet_folder_list+=("${lib#$CURRENT_DIR/}")
	done	
fi

echo $codelet_folder_list

# Build the codelets
for folder in "${codelet_folder_list[@]}"; do
    echo "Building $folder"

	if [ "$SRS_JBPF_DOCKER" -eq 1 ]; then
		DIRECTORY="/codelet"
		$DOCKER_CMD run --rm \
			-v $CURRENT_DIR:/codelet \
			--entrypoint /usr/bin/make \
			--env "USE_JRTC=$USE_JRTC" \
			ghcr.io/microsoft/jrtc-apps/srs-jbpf-sdk:$SDK_IMAGE_TAG \
			-C $DIRECTORY/$folder $OPTIONS 
	else
		DIRECTORY=$(pwd)
		make -C $DIRECTORY/$folder $OPTIONS 
	fi

done

