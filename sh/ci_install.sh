#!/bin/bash

set -e

SH_DIR=$(readlink -f $(dirname "$0"))

"${SH_DIR}/exec.sh" go get -t /wptdashboard/...
