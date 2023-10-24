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
VARIANTS_LIST="- $(echo $VARIANTS_LIST)" # "-" signifies regular package
echo $VARIANTS_LIST

TEMPDIR=$(mktemp -d)
trap 'rm -rf "$TEMPDIR"' EXIT

# generate dependencies-*.log for each extras_require (each in a subproc)
for variant in $VARIANTS_LIST; do
  echo

  if [[ $variant == "-" ]]; then  # regular package (not an extra)
    pip_install_pkg="."
    dockerfile="$TEMPDIR/Dockerfile"
    DEPS_LOG_FILE="dependencies.log"
    SUBTITLE=""
  else
    pip_install_pkg=".[$variant]"
    dockerfile="$TEMPDIR/Dockerfile_$variant"
    DEPS_LOG_FILE="dependencies-${variant}.log"
    SUBTITLE="with the '$variant' extra"
  fi


  cat << EOF >> $dockerfile
FROM python:3.11
COPY . .
RUN pip install --no-cache-dir $pip_install_pkg
CMD []
EOF

  $GITHUB_ACTION_PATH/build-dependencies-dockerfile-logs.sh \
    $(realpath $dockerfile) \
    $DEPS_LOG_FILE \
    $SUBTITLE

done
echo

# # wait for all subprocs
# wait -n # main dependencies.log
# for extra in $VARIANTS_LIST; do
#   wait -n
# done
