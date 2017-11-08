#!/bin/bash

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-"${DOCKER_DIR}/../.."}

# Execute code in docker instance:
#
# -u 0:0             Run as root
# wptd-dev-instance  Name of instance (wptdashboard dev server)

EXEC_STR=""
for ARG in "${@}"; do
  EXEC_STR+="\"${ARG}\" "
done
info "Super-user execute-in-docker:  ${EXEC_STR}"
docker exec -u 0:0 wptd-dev-instance "${@}"
DOCKER_STATUS=${?}
if [ "${DOCKER_STATUS}" != "0" ]; then
  error "Execute-in-docker failed. Is docker instance 'wptd-dev-instance' running?"
else
  info "Execute-in-docker complete."
fi
exit ${DOCKER_STATUS}
