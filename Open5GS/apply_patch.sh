#!/bin/bash
## Copyright (c) Microsoft Corporation. All rights reserved.
# shellcheck disable=SC1091

PATCH_FILE="msr.Open5GS.patch"
SUBM="p3/open5gs"
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"

pushd .
cd "$HERE" || exit 1

sudo rm -rf $SUBM
pushd .
cd ..
git submodule update --init --recursive Open5GS/$SUBM
popd || exit 1

cp $PATCH_FILE $SUBM

cd $SUBM
git apply $PATCH_FILE

rm $PATCH_FILE

popd || exit 1

exit 0
