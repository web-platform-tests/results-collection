#!/bin/bash

# turn on experimental features

# TODO(cvazac) Remove this if/when Server-Timing is enabled by default in Safari
defaults write com.apple.Safari ExperimentalServerTimingEnabled -bool true

echo Closing all instances of the application to ensure the changes
echo are observed.

killall -9 Safari || true
