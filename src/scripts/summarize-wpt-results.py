#!/usr/bin/env python

# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Tool for producing a results summary JSON blobs for a given full report.

Example usage:
./summarize.py --report=full_report.json --out=summary.json
"""

import argparse
import inspect
import json
import logging
import os
import sys

import imp
upload_wpt_results = imp.load_source('upload_wpt_results', 'upload-wpt-results.py')

def main():
    args = parse_flags()  # type: argparse.Namespace

    loggingLevel = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=loggingLevel)
    logger = logging.getLogger()

    summary = {}
    try:
        summary = upload_wpt_results.summarize([args.report])
    except Exception as e:
        logger.fatal('Failed to summarize: %s', e)
        return

    try:
        json.dump(summary, open(args.out, 'w'))
    except Exception as e:
        logger.fatal('Failed to write summary: %s', e)

    logger.info('Saved summary to %s' % args.out)


# Create an ArgumentParser for the flags we'll expect.
def parse_flags():  # type: () -> argparse.Namespace
    # Re-use the docs above as the --help output.
    parser = argparse.ArgumentParser(description=inspect.cleandoc(__doc__))
    parser.add_argument(
        '--report',
        required=True,
        type=str,
        help='Full report input file path')
    parser.add_argument(
        '--out',
        required=True,
        type=str,
        help='Summary report output file path')
    parser.add_argument(
        '--log',
        type=str,
        default='INFO',
        help='Log level to output')
    namespace = parser.parse_args()

    # Check the before and after platform lists have the same length.
    if not os.path.isfile(namespace.report):
        raise ValueError('Report file %s not found.\n' % namespace.before)

    return namespace


if __name__ == '__main__':
    main()
