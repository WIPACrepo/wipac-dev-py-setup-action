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

# use podman to get around user permission issues
sudo apt update
sudo apt-get -y install podman
podman --version

podman build -t my_image --file $1 .

DOCKER_DEPS="dependencies-from-$(basename $1).log"

TEMPDIR="dep-build-$(basename $1)"

# make script
mkdir ./$TEMPDIR
echo "#!/bin/bash" >> ./$TEMPDIR/freezer.sh
echo "whoami" >> ./$TEMPDIR/freezer.sh
echo "chmod +w /local/$TEMPDIR" >> ./$TEMPDIR/freezer.sh
echo "ls -al /local/$TEMPDIR" >> ./$TEMPDIR/freezer.sh
echo "ls -al /local/$TEMPDIR" >> ./$TEMPDIR/freezer.sh
echo "pip3 freeze > /local/$TEMPDIR/$DOCKER_DEPS" >> ./$TEMPDIR/freezer.sh
chmod +x ./$TEMPDIR/freezer.sh

# generate
podman run --rm -i \
    --mount type=bind,source=$(realpath ./$TEMPDIR/),target=/local/$TEMPDIR \
    --userns=keep-id \
    my_image \
    /local/$TEMPDIR/freezer.sh

# grab deps file
# - remove main package since this can cause an infinite loop when a new release is made
if [ ! -z "$PACKAGE_NAME" ]; then
    sed -i "/^$PACKAGE_NAME==/d" ./$TEMPDIR/$DOCKER_DEPS
    sed -i "/^$PACKAGE_NAME /d" ./$TEMPDIR/$DOCKER_DEPS
fi
cat ./$TEMPDIR/$DOCKER_DEPS
# - rename & remove temp dir
mv ./$TEMPDIR/$DOCKER_DEPS $DOCKER_DEPS
rm -r ./$TEMPDIR/
