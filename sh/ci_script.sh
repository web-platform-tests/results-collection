#!/bin/bash

SH_DIR=$(readlink -f $(dirname "$0"))
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-$(readlink -f "${SH_DIR}/..")}

cd "${WPTDASHBOARD_DIR}"

pycodestyle .
python -m unittest discover -p "/wptdashboard/*_test.py"
go test -v ./...
"${GOPATH}/bin/golint" -set_exit_status
