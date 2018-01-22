#!/bin/bash

# Start the Google Cloud web development server in `wptd-dev-instance`
# (started using ./run.sh).

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"
WPTD_PATH=${WPTD_PATH:-"${DOCKER_DIR}/../.."}

info "Selecting gcloud project: wptdashboard"
docker exec -u $(id -u $USER):$(id -g $USER) wptd-dev-instance \
    gcloud config set project wptdashboard
info "Checking application default credentials"
docker exec -u $(id -u $USER):$(id -g $USER) wptd-dev-instance \
    gcloud auth application-default print-access-token
DOCKER_STATUS="${?}"
if [ "${DOCKER_STATUS}" != "0" ]; then
  warn "No credentials yet. Logging in..."
  docker exec -ti -u $(id -u $USER):$(id -g $USER) wptd-dev-instance \
      gcloud auth application-default login
  DOCKER_STATUS="${?}"
  if [ "${DOCKER_STATUS}" != "0" ]; then
    error "Failed to get application default credentials"
    exit "${DOCKER_STATUS}"
  fi
fi
info "Application default credentials installed"
exit "${DOCKER_STATUS}"
