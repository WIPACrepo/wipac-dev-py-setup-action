#!/bin/bash
set -x  # turn on debugging
set -e

########################################################################
#
# install podman using kubic
# https://podman.io/docs/installation#debian
#
########################################################################

sudo mkdir -p /etc/apt/keyrings

# # Debian Testing/Bookworm
# curl -fsSL https://download.opensuse.org/repositories/devel:kubic:libcontainers:unstable/Debian_Testing/Release.key \
#   | gpg --dearmor \
#   | sudo tee /etc/apt/keyrings/devel_kubic_libcontainers_unstable.gpg > /dev/null
# echo \
#   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/devel_kubic_libcontainers_unstable.gpg]\
#     https://download.opensuse.org/repositories/devel:kubic:libcontainers:unstable/Debian_Testing/ /" \
#   | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:unstable.list > /dev/null

podman  --version
podman  info


# Building from Source
sudo apt-get install \
  btrfs-progs \
  crun \
  git \
  golang-go \
  go-md2man \
  iptables \
  libassuan-dev \
  libbtrfs-dev \
  libc6-dev \
  libdevmapper-dev \
  libglib2.0-dev \
  libgpgme-dev \
  libgpg-error-dev \
  libprotobuf-dev \
  libprotobuf-c-dev \
  libseccomp-dev \
  libselinux1-dev \
  libsystemd-dev \
  netavark \
  pkg-config \
  uidmap

go version
echo $PATH

git clone https://github.com/containers/podman/
cd podman
make BUILDTAGS="selinux seccomp" PREFIX=/usr
sudo make install PREFIX=/usr


# Install Podman
# sudo apt-get update
# sudo apt-get -y upgrade
# sudo apt-get -y install podman


podman  --version
podman  info