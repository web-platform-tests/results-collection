#!/bin/bash

set -e

DOCKER_DIR=$(readlink -f $(dirname "$0"))
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(readlink -f "${DOCKER_DIR}/../..")}

cd "${WPTDASHBOARD_DIR}"

echo "ls ${WPTDASHBOARD_DIR}"
ls

docker build -t wptd-base -f Dockerfile.base .
docker build -t wptd-dev -f Dockerfile.dev .
docker run -d -v /etc/group:/etc/group:ro -v /etc/passwd:/etc/passwd:ro \
    -v "$(pwd)":/wptdashboard -u $(id -u $USER):$(id -g $USER) \
    --name wptd-dev-instance wptd-dev /wptdashboard/sh/watch.sh
docker ps -a
