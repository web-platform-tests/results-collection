#!/bin/bash

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

browser_name=$1
url=$2
temp_file=$(mktemp)

install_chromedriver() {
  archive=$1
  target=$PWD/chromedriver

  rm --force $target

  unzip -qq $archive || return 1

  echo $target
}

install_geckodriver() {
  archive=$1
  target=$PWD/geckodriver

  rm --force $target

  tar -xvf $archive >&2 || return 1

  echo $target
}

wget --quiet --output-document $temp_file $url

if [ $? != '0' ]; then
  echo Error downloading browser. >&2
  exit 1
fi

if [ $browser_name == 'chrome' ]; then
  install_chromedriver $temp_file
elif [ $browser_name == 'firefox' ]; then
  install_geckodriver $temp_file
else
  echo Unrecognized browser: $browser_name >&2
  false
fi

result=$?

rm --force $temp_file

exit $result
