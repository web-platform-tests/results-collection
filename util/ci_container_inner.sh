: '
This file runs inside the testrun container
in the context of CI.
'
export WPT_PATH=/web-platform-tests

git clone --depth 1 https://github.com/w3c/web-platform-tests $WPT_PATH

sudo chown -R $(id -u $USER):$(id -g $USER) $HOME

source $WPT_PATH/tools/ci/lib.sh
hosts_fixup

export BUILD_PATH=/wptdashboard
# Run a small directory (4 tests)
export RUN_PATH=battery-status
export WPT_SHA=$(cd $WPT_PATH && git rev-parse HEAD | head -c 10)

export PLATFORM_ID=firefox-57.0-linux
python /wptdashboard/run/jenkins.py
