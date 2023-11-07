#!/bin/bash
set -x  # turn on debugging
set -e

########################################################################
#
# Generate dependencies-*.log for each Dockerfile*
#
########################################################################


# install podman if needed... (grep -o -> 1 if found)
if [[ $(grep -o "USER" ./Dockerfile) ]]; then
    $GITHUB_ACTION_PATH/install-podman.sh
    podman --version
    USE_PODMAN='--podman'
fi


# from each dockerfile...
for f in ./Dockerfile*; do
    echo $f
    $GITHUB_ACTION_PATH/dep-log-from-dockerfile.sh \
        $f \
        "dependencies-from-$(basename $f).log" \
        "within the container built from '$f'" \
        $USE_PODMAN
done