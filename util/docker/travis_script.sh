#!/bin/bash

set -e

DOCKER_DIR=$(dirname "$0")

# WPT Dashboard code tests
docker exec -u $(id -u $USER):$(id -g $USER) wptd-dev-instance \
    "${DOCKER_DIR}/inner/travis_test.sh"

# Jenkins infrastructure e2e tests
docker run \
  -p 4445:4445 \
  --entrypoint "/bin/bash" wptd-testrun-jenkins \
  /wptdashboard/util/docker/inner/travis_jenkins_test.sh
