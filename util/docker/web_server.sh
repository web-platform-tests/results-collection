#!/bin/bash

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-"${DOCKER_DIR}/../.."}

info "Installing web server code dependencies"
docker exec -u 0:0 wptd-dev-instance \
    /bin/bash -c \
    "pip install -r /wptdashboard/requirements.txt && cd /go/src/wptdashboard && go get -t ./..."
DOCKER_STATUS="${?}"
if [ "${DOCKER_STATUS}" != "0" ]; then
  error "Failed to install web server code dependencies"
  exit "${DOCKER_STATUS}"
fi
info "Starting web server. Port forwarded from wptd-dev-instance: 8080"
docker exec -it -u $(id -u $USER):$(id -g $USER) wptd-dev-instance \
       dev_appserver.py --host=0.0.0.0 .
