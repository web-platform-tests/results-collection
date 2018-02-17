#!/bin/bash

# Start Docker-based development server as `wptd-dev-instance` in the
# foreground.

DOCKER_DIR=$(dirname $0)
source "${DOCKER_DIR}/../commands.sh"
source "${DOCKER_DIR}/../logging.sh"
source "${DOCKER_DIR}/../path.sh"
WPTD_PATH=${WPTD_PATH:-$(absdir ${DOCKER_DIR}/../..)}

WPTD_HOST_WEB_PORT=${WPTD_HOST_WEB_PORT:-"8080"}
WPTD_HOST_ADMIN_WEB_PORT=${WPTD_HOST_ADMIN_WEB_PORT:-"8000"}
WPTD_HOST_API_WEB_PORT=${WPTD_HOST_API_WEB_PORT:-"9999"}

WPTD_CONTAINER_HOST
# Create a docker instance:
#
# --rm                                      Auto-remove when stopped
# -it                                       Interactive mode (Ctrl+c will halt
#                                           instance)
# -v "${WPTD_PATH}":/wptdashboard           Mount the repository
# -u $(id -u $USER):$(id -g $USER)          Run as current user and group
# -p "${WPTD_HOST_WEB_PORT}:8080"   Expose web server port
# --name wptd-dev-instance                  Name the instance
# wptd-dev                                  Identify image to use
# /wptdashboard/util/docker/inner/watch.sh  Identify code to execute

info "Creating docker instance for dev server. Instance name: wptd-dev-instance"
docker run -t -d --entrypoint /bin/bash \
    -v "${WPTD_PATH}":/home/jenkins/wptdashboard \
    -u $(id -u $USER):$(id -g $USER) \
    -p "${WPTD_HOST_WEB_PORT}:8080" \
    -p "${WPTD_HOST_ADMIN_WEB_PORT}:8000" \
    -p "${WPTD_HOST_API_WEB_PORT}:9999" \
    --name wptd-dev-instance wptd-dev

wptd_chown "/home/jenkins"
wptd_exec_it "/home/jenkins/wptdashboard/util/docker-dev/inner/watch.sh"
wptd_stop
wptd_rm
