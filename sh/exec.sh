#!/bin/bash

SH_DIR=$(readlink -f $(dirname "$0"))
source "${SH_DIR}/logging.sh"
WPTDASHBOARD_DIR=$(readlink -f "${SH_DIR}/..")

# Execute code in docker instance:
#
# -u $(id -u $USER):$(id -g $USER)  Run as current user and group
# wptdashboard-instance             Name of instance (wptdashboard dev server)

if ! docker exec -u $(id -u $USER):$(id -g $USER) \
  wptdashboard-instance $1 $2 $3 $4 $5 $6 $7 $8 $9; then
  error "Execute-in-docker failed. Is docker instance 'wptdashboard-instance' running?"
fi
