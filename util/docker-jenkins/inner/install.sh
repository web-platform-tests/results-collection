#!/bin/bash

# This file installs for WPT testrun in a container
# in the context of Travis CI.

set -ex

pushd "${WPT_DIR}/.."
git clone --depth 1 https://github.com/w3c/web-platform-tests
popd

source "${WPT_DIR}/tools/ci/lib.sh"
hosts_fixup
