#!/bin/bash

SH_DIR=$(readlink -f $(dirname "$0"))
source "${SH_DIR}/logging.sh"
WPTDASHBOARD_DIR=$(readlink -f "${SH_DIR}/..")

# Create a docker instance:
#
# --rm                                    Auto-remove when stopped
# -it                                     Interactive mode (Ctrl+c will halt instance)
# -v /etc/{group|passwd}:ro               READ-ONLY mount of user/group info on host machine
# -v "${WPTDASHBOARD_DIR}":/wptdashboard  Mount the repository
# -u $(id -u $USER):$(id -g $USER)        Run as current user and group
# --name wptdashboard-instance            Name the instance
# wptdashboard:0.1                        Identify image to use
# /wptdashboard/sh/watch.sh               Identify code to execute

info "Creating docker instance for dev server"
docker run --rm -it -v /etc/group:/etc/group:ro -v /etc/passwd:/etc/passwd:ro \
  -v "${WPTDASHBOARD_DIR}":/wptdashboard -u $(id -u $USER):$(id -g $USER) \
  --name wptdashboard-instance wptdashboard:0.1 /wptdashboard/sh/watch.sh
