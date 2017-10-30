#!/bin/bash

SH_DIR=$(readlink -f $(dirname "$0"))
source "${SH_DIR}/logging.sh"
WPTDASHBOARD_DIR=$(readlink -f "${SH_DIR}/..")

# Execute code in docker instance:
#
# -u 0:0                 Run as root
# wptdashboard-instance  Name of instance (wptdashboard dev server)

EXEC_STR=""
for ARG in "${@}"; do
  EXEC_STR+="\"${ARG}\" "
done
info "Super-user execute-in-docker:  ${EXEC_STR}"
docker exec -u 0:0 wptdashboard-instance "${@}"
DOCKER_STATUS=${?}
if [ "${DOCKER_STATUS}" != "0" ]; then
  error "Execute-in-docker failed. Is docker instance 'wptdashboard-instance' running?"
else
  info "Execute-in-docker complete."
fi
exit ${DOCKER_STATUS}
