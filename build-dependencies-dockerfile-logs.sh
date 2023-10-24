#!/bin/bash
set -x  # turn on debugging
set -e

########################################################################
#
# Generate dependencies-dockerfile*.log for given Dockerfile
#
########################################################################

if [ -z "$1" ]; then
    echo "Usage: build-dependencies-dockerfile-logs.sh DOCKERFILE"
    exit 1
fi
if [ ! -f "$1" ]; then
    echo "File Not Found: $1"
    exit 2
fi


# build
if [ "$2" == "--podman" ]; then
    # use podman to get around user permission issues (with --userns=keep-id:uid=1000,gid=1000)
    podman build -t my_image --file $1 .
else
    docker build -t my_image --file $1 .
fi


DOCKER_DEPS="dependencies-from-$(basename $1).log"
subtitle="within the container built from $(basename $1)"


# move script
TEMPDIR="dep-build-$(basename $1)"
mkdir ./$TEMPDIR
trap 'rm -rf "./$TEMPDIR"' EXIT
cp $GITHUB_ACTION_PATH/make-dependencies-logs.sh $TEMPDIR
chmod +x ./$TEMPDIR/make-dependencies-logs.sh


# generate
if [ "$2" == "--podman" ]; then
    podman run --rm -i \
        --mount type=bind,source=$(realpath ./$TEMPDIR/),target=/local/$TEMPDIR \
        --userns=keep-id:uid=1000,gid=1000 \
        my_image \
        /local/$TEMPDIR/make-dependencies-logs.sh $DOCKER_DEPS $subtitle
else
    docker run --rm -i \
        --mount type=bind,source=$(realpath ./$TEMPDIR/),target=/local/$TEMPDIR \
        my_image \
        /local/$TEMPDIR/make-dependencies-logs.sh $DOCKER_DEPS $subtitle
fi


mv ./$TEMPDIR/$DOCKER_DEPS $DOCKER_DEPS
