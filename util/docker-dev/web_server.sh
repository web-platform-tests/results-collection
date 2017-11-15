#!/bin/bash

# Start the Google Cloud web development server in `wptd-dev-instance`
# (started using ./run.sh).

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"
WPTD_PATH=${WPTD_PATH:-"${DOCKER_DIR}/../.."}

info "Installing web server code dependencies"
docker exec -u $(id -u $USER):$(id -g $USER) wptd-dev-instance make build
DOCKER_STATUS="${?}"
if [ "${DOCKER_STATUS}" != "0" ]; then
  error "Failed to install web server code dependencies"
  exit "${DOCKER_STATUS}"
fi
info "Starting web server. Port forwarded from wptd-dev-instance: 8080"
docker exec -it -u $(id -u $USER):$(id -g $USER) wptd-dev-instance \
    dev_appserver.py --api_port=9999 --host=0.0.0.0 .
