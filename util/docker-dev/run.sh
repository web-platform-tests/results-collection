#!/bin/bash

# Start Docker-based development server as `wptd-dev-instance` in the
# foreground.

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"
source "${DOCKER_DIR}/../path.sh"
WPTD_PATH=${WPTD_PATH:-$(absdir "${DOCKER_DIR}/../..")}

WPTDASHBOARD_HOST_WEB_PORT=${WPTDASHBOARD_HOST_WEB_PORT:-"8080"}

# Create a docker instance:
#
# --rm                                      Auto-remove when stopped
# -it                                       Interactive mode (Ctrl+c will halt
#                                           instance)
# -v /etc/{group|passwd}:ro                 READ-ONLY mount of user/group info
#                                           on host machine
# -v "${WPTD_PATH}":/wptdashboard    Mount the repository
# -u $(id -u $USER):$(id -g $USER)          Run as current user and group
# -p "${WPTDASHBOARD_HOST_WEB_PORT}:8080"   Expose web server port
# --name wptd-dev-instance                  Name the instance
# wptd-dev                                  Identify image to use
# /wptdashboard/util/docker/inner/watch.sh  Identify code to execute

info "Creating docker instance for dev server. Instance name: wptd-dev-instance"
docker run -t -d --entrypoint /bin/bash \
    -v /etc/group:/etc/group:ro \
    -v /etc/passwd:/etc/passwd:ro \
    -v "${WPTD_PATH}":/home/jenkins/wptdashboard \
    -u $(id -u $USER):$(id -g $USER) \
    -p "${WPTDASHBOARD_HOST_WEB_PORT}:8080" \
    --name wptd-dev-instance wptd-dev

docker exec -u 0:0 wptd-dev-instance \
    chown -R $(id -u $USER):$(id -g $USER) /home/jenkins

docker exec -ti -u $(id -u $USER):$(id -g $USER) wptd-dev-instance \
    /home/jenkins/wptdashboard/util/docker-dev/inner/watch.sh

docker stop wptd-dev-instance
docker rm wptd-dev-instance
