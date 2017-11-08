#!/bin/bash

set -e

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-"${DOCKER_DIR}/../.."}

cd "${WPTDASHBOARD_DIR}"

info "Stopping and removing docker instance 'wpt-dev-instance'"
docker stop wptd-dev-instance && docker rm wptd-dev-instance
DOCKER_STATUS=${?}
if [ "${DOCKER_STATUS}" != "0" ]; then
  error "Docker stop-and-remove failed."
else
  info "Docker stop-and-remove complete."
fi
exit ${DOCKER_STATUS}
