: '
This file runs inside a WPT testrun container
in the context of Travis CI.
'

set -e

git clone --depth 1 https://github.com/w3c/web-platform-tests
mv web-platform-tests/* "${WPT_DIR}"
rmdir web-platform-tests

source "${WPT_DIR}/tools/ci/lib.sh"
hosts_fixup

export BUILD_PATH="${WPTDASHBOARD_DIR}"
# Run a small directory (4 tests)
export RUN_PATH=battery-status
export WPT_SHA=$(cd $WPT_PATH && git rev-parse HEAD | head -c 10)

export PLATFORM_ID=firefox-57.0-linux
python /wptdashboard/run/jenkins.py
