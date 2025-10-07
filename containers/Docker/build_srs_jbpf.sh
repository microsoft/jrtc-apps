#!/bin/bash

BASE_IMAGE_TAG=latest
IMAGE_TAG=srsran25.04-latest
CACHE_FLAG=

Usage()
{
   # Display Help
   echo "Build srsRan image"
   echo "options:"
   echo "[-b]    Optional base image tag.  Default='latest'"
   echo "[-s]    Optional image tag.  Default='srsran25.04-latest'"
   echo "[-c]    Optional.  If included, '--no-cache- is added to the Docker build"
   echo
}

# Get the options
while getopts "b:s:c" option; do
	case $option in
		b) # Set image tag
			BASE_IMAGE_TAG="$OPTARG";;
		s) # Set image tag
			IMAGE_TAG="$OPTARG";;
		c) # Set image tag
			CACHE_FLAG="--no-cache";;
		\?) # Invalid option
			echo "Error: Invalid option"
			Usage
			exit 1;;
	esac
done

echo BASE_IMAGE_TAG $BASE_IMAGE_TAG
echo IMAGE_TAG $IMAGE_TAG

docker build $CACHE_FLAG \
    --build-arg BASE_IMAGE_TAG=${BASE_IMAGE_TAG} \
    -t ghcr.io/microsoft/jrtc-apps/srs-jbpf:${IMAGE_TAG} -f SRS-jbpf.Dockerfile .

exit 0
