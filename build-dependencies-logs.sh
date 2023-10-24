#!/bin/bash
set -x  # turn on debugging
set -e

########################################################################
#
# Build dependencies.log and
# generate dependencies-*.log for each extras_require
#
########################################################################


# get all extras
EXTRAS=$(python3 $GITHUB_ACTION_PATH/list_extras.py setup.cfg)

# generate dependencies-*.log for each extras_require (each in a subproc)
for extra in $EXTRAS; do
  echo

  ./Dockerfile << EOF
FROM python:3.11
COPY . .
RUN pip install --no-cache-dir .
CMD []
EOF

  export DEPS_LOG_FILE="dependencies-${extra}.log"
  export SUBTITLE="with the '$extra' extra"
  $GITHUB_ACTION_PATH/build-dependencies-dockerfile-logs.sh $(realpath ./Dockerfile)

done
echo

# # wait for all subprocs
# wait -n # main dependencies.log
# for extra in $EXTRAS; do
#   wait -n
# done
