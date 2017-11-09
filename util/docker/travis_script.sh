#!/bin/bash

set -e

DOCKER_DIR=$(dirname "$0")

# WPT Dashboard code tests
"${DOCKER_DIR}/exec.sh" pycodestyle --exclude=*_pb2.py .
"${DOCKER_DIR}/exec.sh" python -m unittest discover -p '*_test.py'
"${DOCKER_DIR}/exec.sh" go test -v ./...
"${DOCKER_DIR}/exec.sh" golint -set_exit_status

# Jenkins infrastructure e2e tests
docker run \
  -p 4445:4445 \
  --entrypoint "/bin/bash" wptd-testrun-jenkins \
  /wptdashboard/util/docker/inner/travis_jenkins_test.sh
