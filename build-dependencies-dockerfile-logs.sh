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


# make script
TEMPDIR="dep-build-$(basename $1)"
mkdir ./$TEMPDIR
echo "#!/bin/bash" >> ./$TEMPDIR/make_dep_files.sh
# PIP_FREEZE
echo "pip3 freeze > /local/$TEMPDIR/$PIP_FREEZE" >> ./$TEMPDIR/freezer.sh
# PIP_DEP_TREE
echo "pip3 install --target=. pipdeptree" >> ./$TEMPDIR/make_dep_files.sh
echo "./bin/pipdeptree > /local/$TEMPDIR/$PIP_DEP_TREE" >> ./$TEMPDIR/make_dep_files.sh
chmod +x ./$TEMPDIR/make_dep_files.sh


# generate
if [ "$2" == "--podman" ]; then
    podman run --rm -i \
        --mount type=bind,source=$(realpath ./$TEMPDIR/),target=/local/$TEMPDIR \
        --userns=keep-id:uid=1000,gid=1000 \
        my_image \
        /local/$TEMPDIR/make_dep_files.sh
else
    docker run --rm -i \
        --mount type=bind,source=$(realpath ./$TEMPDIR/),target=/local/$TEMPDIR \
        my_image \
        /local/$TEMPDIR/make_dep_files.sh
fi


# grab dep files
# - remove main package since this can cause an infinite loop when a new release is made
if [ ! -z "$PACKAGE_NAME" ]; then
    # PIP_FREEZE
    sed -i "/^$PACKAGE_NAME==/d" ./$TEMPDIR/$PIP_FREEZE
    sed -i "/^$PACKAGE_NAME /d" ./$TEMPDIR/$PIP_FREEZE
    sed -i "/#egg=$PACKAGE_NAME$/d" ./$TEMPDIR/$PIP_FREEZE
    # now if using pip's editable-install (-e), pip converts dashes to underscores
    package_name_dashes_to_underscores=$(echo "$PACKAGE_NAME" | sed -r 's/-/_/g')
    sed -i "/#egg=$package_name_dashes_to_underscores$/d" ./$TEMPDIR/$PIP_FREEZE
    sed -i "/^#/d" ./$TEMPDIR/$PIP_FREEZE  # remove all commented lines  # see comments in https://github.com/pypa/pip/issues/6199

    # PIP_DEP_TREE
    sed -i "s/^$PACKAGE_NAME==.*/$PACKAGE_NAME/g" ./$TEMPDIR/$PIP_DEP_TREE
fi


# combine & cleanup
DOCKER_DEPS="dependencies-from-$(basename $1).log"
cat ./$TEMPDIR/$PIP_FREEZE >> $DOCKER_DEPS
echo "------------------------------------------------------------------------" >> $DOCKER_DEPS
cat ./$TEMPDIR/$PIP_DEP_TREE >> $DOCKER_DEPS
rm -r ./$TEMPDIR/
