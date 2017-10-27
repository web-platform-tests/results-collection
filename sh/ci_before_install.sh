#!/bin/bash

SH_DIR=$(readlink -f $(dirname "$0"))
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(readlink -f "${SH_DIR}/..")}

cd "${WPTDASHBOARD_DIR}"

docker build -t wptdashboard:0.1 .
docker run --rm -v /etc/group:/etc/group:ro -v /etc/passwd:/etc/passwd:ro -v "$(pwd)":/wptdashboard -u $(id -u $USER):$(id -g $USER) --name wptdashboard-instance wptdashboard:0.1 /wptdashboard/sh/watch.sh &
docker ps -a
