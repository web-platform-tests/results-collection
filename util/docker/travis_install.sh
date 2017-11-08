#!/bin/bash

set -e

DOCKER_DIR=$(dirname "$0")

"${DOCKER_DIR}/su_exec.sh" /bin/bash -c "cd /go/src/wptdashboard && go get -t ./..."
