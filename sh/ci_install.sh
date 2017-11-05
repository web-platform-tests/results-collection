#!/bin/bash

set -e

SH_DIR=$(readlink -f $(dirname "$0"))

"${SH_DIR}/su_exec.sh" /bin/bash -c "cd /go/src/wptdashboard && go get -t ./..."
