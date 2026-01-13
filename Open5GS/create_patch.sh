
#!/bin/bash
## Copyright (c) Microsoft Corporation. All rights reserved.
# shellcheck disable=SC1091

set -x

PATCH_FILE="msr.Open5GS.patch"
SUBM="p3/open5gs"

# Ensure debugging is turned off on script exit
trap 'set +x' EXIT

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"

pushd .
cd "$HERE" || exit 1

pushd .
cd $SUBM
find .  -type d -name ".venv" |xargs rm -rf
find .  -type d -name "__pycache__" |xargs rm -rf
git add -A
git diff --cached > $HERE/$PATCH_FILE
popd || exit 1

popd || exit 1

exit 0
