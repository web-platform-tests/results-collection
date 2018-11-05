#!/bin/bash

max_wait=10

if ! defaults read com.apple.Safari > /dev/null 2>&1; then
  echo Application defaults are not present, so modifications would be
  echo over-written when the application is next run. Starting the application
  echo in order to initialize defaults.

  /Applications/Safari.app/Contents/MacOS/Safari &

  safari_pid=$!

  count=0
  while ! defaults read com.apple.Safari > /dev/null 2>&1; do
    sleep 1
    count=$((count + 1))

    if [ $count -gt $max_wait ]; then
      echo Error: defaults not written after $max_wait seconds >&2
      exit 1
    fi
  done

  echo Application defaults created. Terminating process.

  kill -9 $safari_pid
fi

# source:
# https://github.com/web-platform-tests/wpt/blob/1999770b55cb8cdd93dbce0e78e5c94b2ba22e0e/tools/wptrunner/wptrunner/browsers/sauce_setup/safari-prerun.sh
defaults write com.apple.Safari com.apple.Safari.ContentPageGroupIdentifier.WebKit2JavaScriptCanOpenWindowsAutomatically -bool true

echo Closing all instances of the application to ensure the changes
echo are observed.

killall -9 Safari || true
