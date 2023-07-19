#!/bin/bash

########################################################################
#
# Build dependencies.log,
# generate dependencies-*.log for each extras_require, and
# commit changes
#
########################################################################

pip3 install pip-tools

# do main dependencies.log in subproc
echo
file="dependencies.log"
echo $file
git mv requirements.txt $file || true  # don't want requirements.txt
echo "pip-compile..."
pip-compile --upgrade --output-file="$file" &
git add $file
git commit -m "<bot> update ${file}" || true  # fails if no change

# get all extras
EXTRAS=$(python3 $GITHUB_ACTION_PATH/list_extras.py setup.cfg)

# generate dependencies-*.log for each extras_require (each in a subproc)
for extra in $EXTRAS; do
  echo
  file="dependencies-${extra}.log"
  echo $file
  git mv "requirements-${extra}.txt" $file || true  # don't want requirements*.txt
  echo "pip-compile..."
  pip-compile --upgrade --extra $extra --output-file="$file" &
  git add $file
  git commit -m "<bot> update ${file}" || true  # fails if no change
done
echo

# wait for all subprocs
wait -n # main dependencies.log
for extra in $EXTRAS; do
  wait -n
done
