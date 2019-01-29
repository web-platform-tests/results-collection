#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
import argparse
import sys

sigil = ' # inserted by extend-hosts.py script'


def main(filename, stream):
    '''Insert newline-separated content into a file, replacing any content that
    was previously inserted using this script. Assumes that the "hash"
    character (`#`) signifies a comment and that appending it to the input will
    not change the semantics of the modified file.

    This script is intended to modify the `/etc/hosts` file on Unix-like
    systems in an idempotent way.'''

    persisting = []
    newly_added = []

    with open(filename) as handle:
        for line in handle:
            line = line.strip()

            if line.endswith(sigil):
                continue

            persisting.append(line)

    for line in stream:
        newly_added.append(line.strip() + sigil)

    with open(filename, 'w') as handle:
        handle.write('\n'.join(persisting + newly_added))


parser = argparse.ArgumentParser(description=main.__doc__)
parser.add_argument('filename')

if __name__ == '__main__':
    main(parser.parse_args().filename, sys.stdin)
