#!/bin/bash

set -e

DOCKER_DIR=$(readlink -f $(dirname "$0"))
source "${DOCKER_DIR}/../logging.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(readlink -f "${DOCKER_DIR}/../..")}

# Execute code in docker instance:
#
# -it                               Run with interactive TTY
# -u $(id -u $USER):$(id -g $USER)  Run as current user and group
# wptd-dev-instance                 Name of instance (wptdashboard dev server)

EXEC_STR=""
for ARG in "${@}"; do
  EXEC_STR+="\"${ARG}\" "
done
info "Execute-in-docker (interactive):  ${EXEC_STR}"
docker exec -it -u $(id -u $USER):$(id -g $USER) wptd-dev-instance "${@}"
DOCKER_STATUS=${?}
exit ${DOCKER_STATUS}
