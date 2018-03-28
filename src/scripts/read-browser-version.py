#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import re
import subprocess


def firefox(binary):
    '''Determine the version of a provided Mozilla Firefox binary, e.g.:

    Channel      | Output                 | Version
    -------------|------------------------|--------
    Experimental | Mozilla Firefox 61.0a1 | 61.0a1
    Stable       | Mozilla Firefox 59.0.2 | 59.0.2
    '''

    stdout = subprocess.check_output([binary, '--version']).strip()

    match = re.match('Mozilla Firefox (\d+\.\d+\.\d+|\d+\.[0-9a-z]+)', stdout)

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

    match = re.match('Google Chrome (\d+\.\d+\.\d+\.\d+)', stdout)

    if not match:
        raise ValueError(
            'Could not find Chrome version number in "%s"' % stdout
        )

    return match.group(1)


parser = argparse.ArgumentParser(description='''Find the version number of the
                                                supplied binary''')
parser.add_argument('--browser-name',
                    choices=('firefox', 'chrome'),
                    required=True)
parser.add_argument('--binary',
                    required=True)

if __name__ == '__main__':
    args = parser.parse_args()

    read = firefox if args.browser_name == 'firefox' else chrome

    print read(args.binary)
