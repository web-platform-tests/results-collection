#!/bin/bash

set -e

DOCKER_DIR=$(readlink -f $(dirname "$0"))
source "${DOCKER_DIR}/../logging.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(readlink -f "${DOCKER_DIR}/../..")}

cd "${WPTDASHBOARD_DIR}"

info "Stopping and removing docker instance 'wpt-travis-instance'"
docker stop wptd-travis-instance && docker rm wptd-travis-instance
DOCKER_STATUS=${?}
if [ "${DOCKER_STATUS}" != "0" ]; then
  error "Docker stop-and-remove failed."
else
  info "Docker stop-and-remove complete."
fi
exit ${DOCKER_STATUS}
