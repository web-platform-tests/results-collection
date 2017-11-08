#!/bin/bash

set -e

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../path.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(absdir "${DOCKER_DIR}/../..")}

cd "${WPTDASHBOARD_DIR}"

docker build -t wptd-base -f Dockerfile.base .
docker build -t wptd-dev -f Dockerfile.dev .
docker run -d -v /etc/group:/etc/group:ro -v /etc/passwd:/etc/passwd:ro \
    -v "$(pwd)":/wptdashboard -u $(id -u $USER):$(id -g $USER) \
    --name wptd-dev-instance wptd-dev /wptdashboard/util/docker/inner/watch.sh
docker ps -a
