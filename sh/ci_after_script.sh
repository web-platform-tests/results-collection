#!/bin/bash

set -e

SH_DIR=$(readlink -f $(dirname "$0"))
source "${SH_DIR}/logging.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(readlink -f "${SH_DIR}/..")}

cd "${WPTDASHBOARD_DIR}"

info "Stopping and removing docker instance 'wptdashboard-instance'"
docker stop wptdashboard-instance && docker rm wptdashboard-instance
DOCKER_STATUS=${?}
if [ "${DOCKER_STATUS}" != "0" ]; then
  error "Docker stop-and-remove failed."
else
  info "Docker stop-and-remove complete."
fi
exit ${DOCKER_STATUS}
