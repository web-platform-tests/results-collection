#!/bin/bash

set -e

docker exec -u 0:0 wptd-dev-instance \
    /bin/bash -c "cd /go/src/wptdashboard && go get -t ./..."
