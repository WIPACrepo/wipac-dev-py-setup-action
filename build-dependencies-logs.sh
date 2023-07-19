#!/bin/bash

########################################################################
#
# Build dependencies.log and
# generate dependencies-*.log for each extras_require
#
########################################################################

pip3 install pip-tools

# do main dependencies.log in subproc
echo
echo "dependencies.log"
git mv requirements.txt dependencies.log || true
echo "pip-compile..."
pip-compile --upgrade --output-file="dependencies.log" &

# get all extras
EXTRAS=$(python3 $GITHUB_ACTION_PATH/list_extras.py setup.cfg)

# generate dependencies-*.log for each extras_require (each in a subproc)
for extra in $EXTRAS; do
  echo
  extra_dep_log="dependencies-${extra}.log"
  echo $extra_dep_log
  git mv "requirements-${extra}.txt" $extra_dep_log || true
  echo "pip-compile..."
  pip-compile --upgrade --extra $extra --output-file="$extra_dep_log" &
done
echo

# wait for all subprocs
wait -n # main dependencies.log
for extra in $EXTRAS; do
  wait -n
done
