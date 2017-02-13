#!/bin/sh -e

unset GIT_DIR
cd /home/ateska/Workspace/seacat/server

git pull
git submodule update --init --recursive

echo -n "GIT_VERSION: "
git describe --abbrev=7 --tags --dirty --always

BE_MONGO=1 ./utils/build-debug.sh CentOS67 x86-64
BE_MONGO=1 ./utils/build-release.sh CentOS67 x86-64
