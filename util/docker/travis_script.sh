#!/bin/bash

set -e

DOCKER_DIR=$(dirname "$0")

"${DOCKER_DIR}/exec.sh" pycodestyle --exclude=*_pb2.py .
"${DOCKER_DIR}/exec.sh" python -m unittest discover -p '*_test.py'
"${DOCKER_DIR}/exec.sh" go test -v ./...
"${DOCKER_DIR}/exec.sh" golint -set_exit_status
