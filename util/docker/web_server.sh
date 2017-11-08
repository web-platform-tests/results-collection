#!/bin/bash

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-"${DOCKER_DIR}/../.."}

# Create a docker instance:
#
# --rm                                     Auto-remove when stopped
# -it                                      Interactive mode (Ctrl+c will halt
#                                          instance)
# -v /etc/{group|passwd}:ro                READ-ONLY mount of user/group info
#                                          on host machine
# -v "${WPTDASHBOARD_DIR}":/wptdashboard   Mount the repository
# -u 0:0                                   Run as root
# -p "${WPTDASHBOARD_HOST_WEB_PORT}:8080"  Expose web server port
# --name wptd-web-server                   Name the instance
# wptd-dev                                 Identify image to use
# /bin/bash -C "..."                       Setup and run web server

info "Installing web server code dependencies"
"${DOCKER_DIR}/su_exec.sh" /bin/bash -c "pip install -r /wptdashboard/requirements.txt && cd /go/src/wptdashboard && go get -t ./..."
DOCKER_STATUS="${?}"
if [ "${DOCKER_STATUS}" != "0" ]; then
  error "Failed to install web server code dependencies"
  exit "${DOCKER_STATUS}"
fi
info "Starting web server"
"${DOCKER_DIR}/i_exec.sh" dev_appserver.py --host=0.0.0.0 .
