#!/bin/bash

SH_DIR=$(readlink -f $(dirname "$0"))
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(readlink -f "${SH_DIR}/..")}

cd "${WPTDASHBOARD_DIR}"

go get -t /wptdashboard/...
go get -u github.com/golang/lint/golint
