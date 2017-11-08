#!/bin/bash

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-"${DOCKER_DIR}/../.."}

WPTDASHBOARD_HOST_WEB_PORT=${WPTDASHBOARD_HOST_WEB_PORT:-"8080"}

# Create a docker instance:
#
# --rm                                      Auto-remove when stopped
# -it                                       Interactive mode (Ctrl+c will halt
#                                           instance)
# -v /etc/{group|passwd}:ro                 READ-ONLY mount of user/group info
#                                           on host machine
# -v "${WPTDASHBOARD_DIR}":/wptdashboard    Mount the repository
# -u $(id -u $USER):$(id -g $USER)          Run as current user and group
# -p "${WPTDASHBOARD_HOST_WEB_PORT}:8080"   Expose web server port
# --name wptd-dev-instance                  Name the instance
# wptd-dev                                  Identify image to use
# /wptdashboard/util/docker/inner/watch.sh  Identify code to execute

info "Creating docker instance for dev server"
docker run --rm -it -v /etc/group:/etc/group:ro -v /etc/passwd:/etc/passwd:ro \
    -v "${WPTDASHBOARD_DIR}":/wptdashboard -u $(id -u $USER):$(id -g $USER) \
    -p "${WPTDASHBOARD_HOST_WEB_PORT}:8080" \
    --name wptd-dev-instance wptd-dev /wptdashboard/util/docker/inner/watch.sh
