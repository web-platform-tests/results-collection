#!/usr/bin/python3

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tool for adding a run from production data as a local TestRun entity in
the Datastore.

Example usage:
./add_production-run.py --sha=b952881825
"""

import argparse
import certifi
import http
import inspect
import json
import logging
import os

from urllib.parse import urlencode
import urllib3

here = os.path.dirname(__file__)


def main():
    args = parse_flags()  # type: argparse.Namespace

    loggingLevel = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=loggingLevel)

    sha = args.sha  # type: str

    pool = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())
    encoded_args = urlencode({'sha': sha})
    url = 'https://wpt.fyi/api/runs?' + encoded_args

    # type: urllib3.response.HTTPResponse
    response = pool.request('GET', url)

    if response.status != 200:
        logging.warning('Failed to fetch %s' % (url))
        return
    logging.debug('Processing JSON from %s' % (url))
    tests = json.loads(response.data.decode('utf-8'))

    for test in tests:
        encoded_args = urlencode({
            'sha': test['revision'],
            'browser': test['browser_name']
        })
        url = 'http://localhost:8080/api/run?' + encoded_args
        response = pool.request('GET', url)
        if response.status != 404:
            logging.warning('Skipping TestRun %s@%s (already present)\n'
                            % (test['browser_name'], test['revision']))
            continue

        post_url = ('http://localhost:8080/api/run?'
                    + urlencode({'retroactive': True}))
        try:
            response = pool.request(
                'POST',
                post_url,
                body=json.dumps(test),
                headers={'Content-Type': 'application/json'})
        except IOError:
            logging.warning("Failed to POST %s" % (post_url))
            continue

        if response.status == http.client.CREATED:
            logging.info("Successfully created TestRun %s@%s"
                         % (test['browser_name'], test['revision']))
        logging.info("%s\n" % (response.data.decode('utf-8')))


# Create an ArgumentParser for the flags we'll expect.
def parse_flags():  # type: () -> argparse.Namespace
    # Re-use the docs above as the --help output.
    parser = argparse.ArgumentParser(description=inspect.cleandoc(__doc__))
    parser.add_argument(
        '--sha',
        default='latest',
        help='SHA[0:10] of the run to fetch')
    parser.add_argument(
        '--log',
        type=str,
        default='INFO',
        help='Log level to output')
    return parser.parse_args()


if __name__ == '__main__':
    main()
