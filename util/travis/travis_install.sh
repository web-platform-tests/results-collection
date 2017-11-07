#!/bin/bash

set -e

TRAVIS_DIR=$(readlink -f $(dirname "$0"))
DOCKER_DIR=${DOCKER_DIR:-$(readlink -f "${TRAVIS_DIR}/../docker")}

"${DOCKER_DIR}/su_exec.sh" /bin/bash -c "cd /go/src/wptdashboard && go get -t ./..."
