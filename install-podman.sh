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


# https://computingforgeeks.com/how-to-install-podman-on-ubuntu/?expand_article=1

echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${VERSION_ID}/ /" | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list
curl -L "https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_${VERSION_ID}/Release.key" | sudo apt-key add -


# Install Podman
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install podman


podman  --version
podman  info