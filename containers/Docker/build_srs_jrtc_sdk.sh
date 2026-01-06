#!/bin/bash

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

IMAGE_TAG=latest

# First build the jrtc image

# TBD: This is a placeholder for the actual build process

# Then, build a small SDK based on the other two
docker build --no-cache\
    -t ghcr.io/microsoft/jrtc-apps/srs-jrtc-sdk:${IMAGE_TAG} -f SRS-jrtc-sdk.Dockerfile .

exit 0

