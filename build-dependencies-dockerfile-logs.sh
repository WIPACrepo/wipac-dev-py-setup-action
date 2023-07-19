#!/bin/bash

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


docker build -t my_image --file $1 .

DOCKER_DEPS="dependencies-from-$(basename $1).log"

TEMPDIR="dep-build-$(basename $1)"

# make script
mkdir ./$TEMPDIR
echo "pip3 freeze > /local/$TEMPDIR/$DOCKER_DEPS" > ./$TEMPDIR/freezer.sh
chmod +x ./$TEMPDIR/freezer.sh

# generate
docker run --rm -i \
    --mount type=bind,source=$(realpath ./$TEMPDIR/),target=/local/$TEMPDIR \
    my_image \
    /local/$TEMPDIR/freezer.sh

# grab deps file
cat ./$TEMPDIR/$DOCKER_DEPS
mv ./$TEMPDIR/$DOCKER_DEPS $DOCKER_DEPS
rm -r ./$TEMPDIR/
