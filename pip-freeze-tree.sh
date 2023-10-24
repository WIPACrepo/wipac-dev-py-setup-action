#!/bin/bash
set -x  # turn on debugging
set -e

########################################################################
#
# Generate dependencies log for given environment
#
########################################################################

if [ -z "$1" ]; then
    echo "Usage: pip-freeze-tree.sh DEPS_FILE [SUBTITLE]"
    exit 1
fi
deps_file=$1

if [ -z "$2" ]; then
    subtitle=""
else
    subtitle=" $2"
fi


pip_freeze='pip_freeze.txt'
trap 'rm "$pip_freeze"' EXIT
pip_dep_tree='pip_dep_tree.txt'
trap 'rm "$pip_dep_tree"' EXIT


# pip_freeze
pip3 freeze > $pip_freeze
# pip_dep_tree
pip3 install --target=. --upgrade pipdeptree
./bin/pipdeptree > $pip_dep_tree


# modify main package listing -> otherwise causes infinite loop when a new release is made
if [ ! -z "$PACKAGE_NAME" ]; then
    # pip_freeze
    # - remove listing all together
    sed -i "/^$PACKAGE_NAME==/d" $pip_freeze
    sed -i "/^$PACKAGE_NAME /d" $pip_freeze
    sed -i "/#egg=$PACKAGE_NAME$/d" $pip_freeze
    # now if using pip's editable-install (-e), pip converts dashes to underscores
    package_name_dashes_to_underscores=$(echo "$PACKAGE_NAME" | sed -r 's/-/_/g')
    sed -i "/#egg=$package_name_dashes_to_underscores$/d" $pip_freeze

    sed -i "/^#/d" $pip_freeze  # remove all commented lines  # see comments in https://github.com/pypa/pip/issues/6199

    # pip_dep_tree
    # - strip version tag
    sed -i "s/^$PACKAGE_NAME==.*/$PACKAGE_NAME/g" $pip_dep_tree
fi


# combine & cleanup
echo "#" >> $deps_file
echo "# This file was autogenerated$subtitle with `python -V`." >> $deps_file
echo "#" >> $deps_file
echo "########################################################################" >> $deps_file
echo "#  pip freeze" >> $deps_file
echo "########################################################################" >> $deps_file
cat $pip_freeze >> $deps_file
echo "########################################################################" >> $deps_file
echo "#  pipdeptree" >> $deps_file
echo "########################################################################" >> $deps_file
cat $pip_dep_tree >> $deps_file
cat $deps_file
