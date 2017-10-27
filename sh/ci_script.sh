#!/bin/bash

set -e

SH_DIR=$(readlink -f $(dirname "$0"))

"${SH_DIR}/exec.sh" pycodestyle --exclude=*_pb2.py .
"${SH_DIR}/exec.sh" python -m unittest discover -p "./*_test.py"
"${SH_DIR}/exec.sh" go test -v ./...
"${SH_DIR}/exec.sh" golint -set_exit_status
