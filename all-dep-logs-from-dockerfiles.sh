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
    nametag=$(echo $DOCKERFILE_NAMETAGS | grep -o "\b$f\:[^[:space:]]*\b" | cut -d ':' -f2-)
    $GITHUB_ACTION_PATH/dep-log-from-dockerfile.sh \
        $f \
        "dependencies-from-$(basename $f).log" \
        "within the container built from '$f'" \
        $nametag \
        $USE_PODMAN
done