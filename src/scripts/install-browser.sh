#!/bin/bash

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

browser_name=$1
url=$2
temp_file=$(mktemp)

install_chrome() {
  deb_archive=$1

  # > Note: Installing Google Chrome will add the Google repository so your
  # > system will automatically keep Google Chrome up to date. If you don’t
  # > want Google's repository, do “sudo touch /etc/default/google-chrome”
  # > before installing the package.
  #
  # Source: https://www.google.com/intl/en/chrome/browser/
  rm --force /etc/default/google-chrome
  touch /etc/default/google-chrome

  # If the environment provides an installation of Google Chrome, the
  # existing binary may take precedence over the one introduced in this
  # script. Remove any previously-existing "alternatives" prior to
  # installation in order to ensure that the new binary is installed as
  # intended.
  if update-alternatives --list google-chrome >&2 ; then
    update-alternatives --remove-all google-chrome || return 1
  fi

  # Installation will fail in cases where the package has unmet dependencies.
  # When this occurs, attempt to use the system package manager to fetch the
  # required packages and retry.
  if ! dpkg --install $deb_archive >&2 ; then
    apt-get install --fix-broken --yes >&2 || return 1
    dpkg --install $deb_archive >&2 || return 1
  fi

  which google-chrome
}

install_firefox() {
  archive=$1
  install_dir=$(readlink --canonicalize ./firefox)

  rm --recursive --force $install_dir

  tar -xvf $archive >&2 || return 1

  chown --recursive $SUDO_USER $install_dir >&2 || return 1

  echo $install_dir/firefox
}

install_safari_technology_preview() {
  archive=$1
  application_dir='/Applications/Safari Technology Preview.app'

  # Remove previously-installed version, if present
  rm -rf $application_dir

  # Install package
  # http://commandlinemac.blogspot.com/2008/12/installing-dmg-application-from-command.html
  output=$(hdiutil mount $archive | tee /dev/stderr)
  device=$(echo "$output" | grep Apple_partition_scheme | awk '{ print $1; }')
  installer \
    -package '/Volumes/Safari Technology Preview/Safari Technology Preview.pkg' \
    -target '/Volumes/Macintosh HD' >&2 || return 1
  result=$?

  # Use the `detach` sub-command (rather than `unmount`) so that the disk image
  # does not remain attached to an entry in `/dev` (and the corresponding
  # `diskimages-helper` process exits).
  #
  # https://stackoverflow.com/questions/4046019/error-when-detaching-volume-using-hdiutil-on-os-x
  hdiutil detach ${device} >&2

  if [ $result != '0' ]; then
    return 1
  fi

  echo "${application_dir}/Contents/MacOS/Safari Technology Preview"
}

# Prefer `curl` over `wget` because `wget` is not included in macOS High Sierra
curl --silent --show-error --output $temp_file $url

if [ $? != '0' ]; then
  echo Error downloading browser. >&2
  exit 1
fi

if [ $browser_name == 'chrome' ]; then
  install_chrome $temp_file
elif [ $browser_name == 'firefox' ]; then
  install_firefox $temp_file
elif [ $browser_name == 'safari' ]; then
  install_safari_technology_preview $temp_file
else
  echo Unrecognized browser: $browser_name >&2
  false
fi

result=$?

rm -f $temp_file

exit $result
