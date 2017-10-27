#!/bin/bash

set -e

SH_DIR=$(readlink -f $(dirname "$0"))
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(readlink -f "${SH_DIR}/..")}

"${SH_DIR}/exec.sh" pycodestyle /wptdashboard
"${SH_DIR}/exec.sh" python -m unittest discover -p "/wptdashboard/*_test.py"
"${SH_DIR}/exec.sh" go test -v /wptdashboard/...
"${SH_DIR}/exec.sh" golint -set_exit_status
