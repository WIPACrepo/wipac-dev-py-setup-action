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



DEPS_LOG_FILE=${DEPS_LOG_FILE:-"dependencies-from-$(basename $1).log"}


# move script
TEMPDIR=$(mktemp -d)
trap 'rm -rf "$TEMPDIR"' EXIT
cp $GITHUB_ACTION_PATH/pip-freeze-tree.sh $TEMPDIR
chmod +x $TEMPDIR/pip-freeze-tree.sh


# generate
if [ "$2" == "--podman" ]; then
    podman run --rm -i \
        --env PACKAGE_NAME=$PACKAGE_NAME \
        --env GITHUB_ACTION_REPOSITORY=$GITHUB_ACTION_REPOSITORY \
        --mount type=bind,source=$(realpath $TEMPDIR/),target=/local/$TEMPDIR \
        --userns=keep-id:uid=1000,gid=1000 \
        my_image \
        /local/$TEMPDIR/pip-freeze-tree.sh /local/$TEMPDIR/$DEPS_LOG_FILE "$SUBTITLE"
else
    docker run --rm -i \
        --env PACKAGE_NAME=$PACKAGE_NAME \
        --env GITHUB_ACTION_REPOSITORY=$GITHUB_ACTION_REPOSITORY \
        --mount type=bind,source=$(realpath $TEMPDIR/),target=/local/$TEMPDIR \
        my_image \
        /local/$TEMPDIR/pip-freeze-tree.sh /local/$TEMPDIR/$DEPS_LOG_FILE "$SUBTITLE"
fi

ls $TEMPDIR
mv $TEMPDIR/$DEPS_LOG_FILE $DEPS_LOG_FILE
