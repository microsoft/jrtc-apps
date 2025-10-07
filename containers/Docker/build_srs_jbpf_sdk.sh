#!/bin/bash

BASE_IMAGE_TAG=latest
IMAGE_TAG=srsran25.04-latest

Usage()
{
   # Display Help
   echo "Build srsRan=Jbpf base image"
   echo "options:"
   echo "[-b]    Optional base image tag.  Default='latest'"
   echo "[-s]    Optional srsRan image tag.  Default='srsran25.04-latest'"
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

# First build the jbpf_protobuf image

pushd . > /dev/null
cd ../../jbpf_protobuf/

# To build for a particular OS, run:
OS=azurelinux
docker build -t jbpfp-$OS:latest -f deploy/$OS.Dockerfile .

# And to create a jbpf_protobuf_cli image from that container, run:
docker build --build-arg builder_image=jbpfp-$OS --build-arg builder_image_tag=latest -t jbpf_protobuf_cli:latest - < deploy/jbpf_protobuf_cli.Dockerfile

popd > /dev/null



docker build $CACHE_FLAG \
  	--build-arg BASE_IMAGE_TAG=${BASE_IMAGE_TAG} \
    --build-arg SRS_JBPF_IMAGE_TAG=${IMAGE_TAG} \
    --build-arg JBPF_PROTOBUF_BUILDER_IMAGE=jbpf_protobuf_cli \
    --build-arg JBPF_PROTOBUF_BUILDER_IMAGE_TAG=latest \
    -t ghcr.io/microsoft/jrtc-apps/srs-jbpf-sdk:${IMAGE_TAG} -f SRS-jbpf-sdk.Dockerfile .

exit 0
