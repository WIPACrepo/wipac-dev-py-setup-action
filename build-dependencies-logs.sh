#!/bin/bash
set -x  # turn on debugging
set -e

########################################################################
#
# Build dependencies.log and
# generate dependencies-*.log for each extras_require
#
########################################################################

pip3 install --upgrade pip
pip3 install pip-tools

PIPTOOLSCACHE=./pip-tools-cache
mkdir -p $PIPTOOLSCACHE
trap 'rm -rf "$PIPTOOLSCACHE"' EXIT

# do main dependencies.log in subproc
echo
file="dependencies.log"
echo $file
git mv requirements.txt $file 2> /dev/null || true  # don't want requirements.txt
echo "pip-compile..."
pip-compile --upgrade --output-file="$file" --cache-dir="$PIPTOOLSCACHE/$(echo $file | sed -r 's/\./-/g')" &

# get all extras
EXTRAS=$(python3 $GITHUB_ACTION_PATH/list_extras.py setup.cfg)

# generate dependencies-*.log for each extras_require (each in a subproc)
for extra in $EXTRAS; do
  echo
  file="dependencies-${extra}.log"
  echo $file
  git mv "requirements-${extra}.txt" $file 2> /dev/null || true  # don't want requirements*.txt
  echo "pip-compile..."
  pip-compile --upgrade --extra $extra --output-file="$file" --cache-dir="$PIPTOOLSCACHE/$(echo $file | sed -r 's/\./-/g')" &
done
echo

# wait for all subprocs
wait -n # main dependencies.log
for extra in $EXTRAS; do
  wait -n
done
