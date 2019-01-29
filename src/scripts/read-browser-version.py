#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import print_function
import argparse
import os
import re
import subprocess
import xml.etree.ElementTree


def firefox(binary):
    '''Determine the version of a provided Mozilla Firefox binary, e.g.:

    Channel      | Output                 | Version
    -------------|------------------------|--------
    Experimental | Mozilla Firefox 61.0a1 | 61.0a1
    Stable       | Mozilla Firefox 59.0.2 | 59.0.2
    '''

    stdout = subprocess.check_output([binary, '--version']).strip()

    match = re.match(r'Mozilla Firefox (\d+\.\d+\.\d+|\d+\.[0-9a-z]+)', stdout)

    if not match:
        raise ValueError(
            'Could not find Firefox version number in "%s"' % stdout
        )

    return match.group(1)


def chrome(binary):
    '''Determine the version of a provided Google Chrome binary, e.g.:

    Output                      | Version
    ----------------------------|--------------
    Google Chrome 65.0.3325.181 | 65.0.3325.181
    '''
    stdout = subprocess.check_output([binary, '--version']).strip()

    match = re.match(r'Google Chrome (\d+\.\d+\.\d+\.\d+)', stdout)

    if not match:
        raise ValueError(
            'Could not find Chrome version number in "%s"' % stdout
        )

    return match.group(1)


def safari(binary):
    '''Determine the version of a provided Safari binary.'''

    # The Safari binary cannot be queried for this information. Because it may
    # only be installed at the system level, this function operates on
    # assumptions regarding files that are present relative to the binary.
    # The XML-formatted `version.plist` file contains key/value pairs in the
    # following structure:
    #
    #     <plist version="1.0">
    #     <dict>
    #         <key>EXAMPLE KEY</key>
    #         <string>EXAMPLE VALUE</string>
    #     </dict>
    #     </plist>
    #
    # See:
    # https://developer.apple.com/library/content/documentation/General/Reference/InfoPlistKeyReference/Articles/AboutInformationPropertyListFiles.html#//apple_ref/doc/uid/TP40009254-SW1

    version_file = os.path.normpath(os.path.join(
        os.path.realpath(binary), os.pardir, os.pardir, 'version.plist'
    ))

    try:
        root = xml.etree.ElementTree.parse(version_file).getroot()
    except IOError:
        raise ValueError('Could not locate file: %s' % version_file)

    values = {}
    name = None

    for node in root.find('dict'):
        if not name:
            if node.tag != 'key':
                raise ValueError(
                    'Unexpected data structure in %s' % version_file
                )

            name = node.text
        else:
            values[name] = node.text
            name = None

    version = values.get('CFBundleShortVersionString')

    if not version:
        raise ValueError(
            'Could not find Safari version in %s' % version_file
        )

    return version


parser = argparse.ArgumentParser(description='''Find the version number of the
                                                supplied binary''')
parser.add_argument('--browser-name',
                    choices=('firefox', 'chrome', 'safari'),
                    required=True)
parser.add_argument('--binary',
                    required=True)

if __name__ == '__main__':
    args = parser.parse_args()

    read = {
        'firefox': firefox,
        'chrome': chrome,
        'safari': safari
    }.get(args.browser_name)

    print(read(args.binary))
