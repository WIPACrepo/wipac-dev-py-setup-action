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
VARIANTS_LIST=$(python3 $GITHUB_ACTION_PATH/list_extras.py setup.cfg)
VARIANTS_LIST="$(echo $VARIANTS_LIST) -"
echo $VARIANTS_LIST

# generate dependencies-*.log for each extras_require (each in a subproc)
for variant in $VARIANTS_LIST; do
  echo

  if [[ $variant == "-" ]]; then  # not an extra
    pip_install_pkg="."
    dockerfile="./Dockerfile"
    export DEPS_LOG_FILE="dependencies.log"
    export SUBTITLE=""
  else
    pip_install_pkg=".[$variant]"
    dockerfile="./Dockerfile_$variant"
    export DEPS_LOG_FILE="dependencies-${variant}.log"
    export SUBTITLE="with the '$variant' extra"
  fi
  trap 'rm "$dockerfile"' EXIT

  cat << EOF >> $dockerfile
FROM python:3.11
COPY . .
RUN pip install --no-cache-dir $pip_install_pkg
CMD []
EOF

  $GITHUB_ACTION_PATH/build-dependencies-dockerfile-logs.sh $(realpath $dockerfile)

done
echo

# # wait for all subprocs
# wait -n # main dependencies.log
# for extra in $VARIANTS_LIST; do
#   wait -n
# done
