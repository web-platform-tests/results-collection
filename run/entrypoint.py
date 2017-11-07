import argparse
import gzip
import json
import platform as host_platform
import re
import subprocess
import sys
import os

"""
Runs WPT and uploads results. More specifically:

1. Runs tests using `wpt run`.
2. Uploads summary and individual file results to GCS as gzipped JSON.
3. POSTs to wpt.fyi/test-runs to create a new test run entry.

The dependencies setup and running portion of this script are intentionally
be left small. The brunt of the work should take place in WPT's `wpt run`.
See https://github.com/w3c/web-platform-tests/blob/master/wpt.py.
"""


def main(args):
    print('args:', args)
    # platform = get_and_validate_platform(args.platform_id)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'platform_id',
        help='A platform ID, specified as keys in browsers.json.'
    )
    parser.add_argument(
        '--path',
        help='WPT path to run. If not specified, runs all WPT.',
        default=''
    )
    parser.add_argument(
        '--upload',
        help='Upload results to Google Storage.',
        action='store_true'
    )
    parser.add_argument(
        '--create-testrun',
        help=('Creates a new TestRun in the Dashboard. '
              'Results from this run will be automatically '
              'promoted if "initially_loaded" is true for the '
              'browser in browsers.json.'),
        action='store_true'
    )
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main(parse_args())
