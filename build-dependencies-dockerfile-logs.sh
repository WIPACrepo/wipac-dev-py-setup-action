#!/bin/bash

########################################################################
#
# Generate dependencies-dockerfile*.log for each Dockerfile present and
# commit changes
#
########################################################################

docker build -t my_image .

DOCKER_DEPS="dependencies-from-dockerfile.log"

TEMPDIR="dep-build"

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

# commit
git add $DOCKER_DEPS
git commit -m "<bot> update ${DOCKER_DEPS}" || true  # fails if no change
