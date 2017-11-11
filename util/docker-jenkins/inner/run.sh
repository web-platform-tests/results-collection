#!/bin/bash

# This file runs inside a WPT testrun container
# in the context of Travis CI.

set -x

export BUILD_PATH="${WPTDASHBOARD_DIR}"
# Run a small directory (4 tests)
export RUN_PATH=battery-status
export WPT_SHA=$(cd $WPT_PATH && git rev-parse HEAD | head -c 10)

export PLATFORM_ID=firefox-57.0-linux
python "${WPTDASHBOARD_DIR}/run/jenkins.py"
