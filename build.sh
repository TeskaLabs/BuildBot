#!/bin/sh -e

cd /home/ateska/Workspace/seacat/server
git pull
git submodule update --init --recursive

BE_MONGO=1 ./utils/build-debug.sh CentOS67 x86-64
BE_MONGO=1 ./utils/build-release.sh CentOS67 x86-64