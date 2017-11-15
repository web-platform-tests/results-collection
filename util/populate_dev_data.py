#!/usr/bin/env python

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Tool for adding some data to a datastore using the AppEngine Remote API.
This script adds a Token for 'upload-token' (needed for adding TestRun using
POST requests), and a few statically-server TestRun entries (see /static/).

Example usage:
./populate_dev_data.py
'''

import argparse
import inspect
import logging
import os
import sys

from typing import List
from urllib import urlencode


def main(args):  # type: (argparse.Namespace) -> None
    try:
        import dev_appserver
        dev_appserver.fix_sys_path()
    except ImportError as e:
        print('ERROR: %s\n' % (e))
        print('Please provide --sdk-root, or make sure App Engine SDK is'
              ' in your PYTHONPATH')

    import google.appengine.ext.ndb as ndb
    from google.appengine.ext.remote_api import remote_api_stub

    remote_api_stub.ConfigureRemoteApiForOAuth(
        args.server_uri,
        '/_ah/remote_api',
        secure=args.secure)

    class Token(ndb.Model):
        secret = ndb.StringProperty()

    class TestRun(ndb.Model):
        BrowserName = ndb.StringProperty()
        BrowserVersion = ndb.StringProperty()
        OSName = ndb.StringProperty()
        OSVersion = ndb.StringProperty()
        Revision = ndb.StringProperty()
        ResultsURL = ndb.StringProperty()
        CreatedAt = ndb.DateProperty()

    # Create empty Token 'upload-token'
    secret = Token(id='upload-token', secret='')
    secret.put()
    logging.info('Added Token \'upload-token\' with empty secret.')
    # Add some runs.
    path = '/static/b952881825/%s'
    test_runs = [
        TestRun(
            id='dev-testrun-chrome-63',
            BrowserName='chrome',
            BrowserVersion='63.0',
            OSName='linux',
            OSVersion='3.16',
            Revision='b952881825',
            ResultsURL=path % 'chrome-63.0-linux-summary.json.gz'),
        TestRun(
            id='dev-testrun-edge-15',
            BrowserName='edge',
            BrowserVersion='15',
            OSName='windows',
            OSVersion='10',
            Revision='b952881825',
            ResultsURL=path % 'edge-15-windows-10-sauce-summary.json.gz'),
        TestRun(
            id='dev-testrun-firefox-57',
            BrowserName='firefox',
            BrowserVersion='57.0',
            OSName='linux',
            OSVersion='*',
            Revision='b952881825',
            ResultsURL=path % 'firefox-57.0-linux-summary.json.gz'),
        TestRun(
            id='dev-testrun-safari-10',
            BrowserName='safari',
            BrowserVersion='10',
            OSName='macos',
            OSVersion='10.12',
            Revision='b952881825',
            ResultsURL=path % 'safari-10-macos-10.12-sauce-summary.json.gz'),
    ]  # type: List[TestRun]

    for browser in ['chrome', 'edge', 'firefox', 'safari']:
        jsonURL = ('https://wpt.fyi/results?'
                   + urlencode({'platform': browser}))
        test_runs.append(
            TestRun(
                id=('prod-latest-' + browser),
                BrowserName=browser,
                BrowserVersion='latest',
                Revision='latest',
                ResultsURL=jsonURL))

    for test_run in test_runs:
        test_run.put()
        logging.info('Added TestRun %s' % test_run.key.id())


# Create an ArgumentParser for the flags we'll expect.
def parse_flags():  # type: () -> argparse.Namespace
    # Re-use the docs above as the --help output.
    parser = argparse.ArgumentParser(description=inspect.cleandoc(__doc__))
    parser.add_argument(
        '--log',
        type=str,
        default='INFO',
        help='Log level to output')
    parser.add_argument(
        '--sdk-root',
        type=str,
        dest='sdk_root',
        default='',
        help='Root path to the App Engine SDK installation, if it\'s not'
             'already in your PYTHONPATH')
    parser.add_argument(
        '--creds',
        type=str,
        dest='creds_path',
        default='',
        help='Path to the Application Default Credentials, if it\'s not'
             'already in your enviroment (as GOOGLE_APPLICATION_CREDENTIALS)')
    parser.add_argument(
        '--server',
        type=str,
        dest='server_uri',
        required=True,
        help='Base URI for the Remote API endpoint. Note that you can set the '
             'port when running the dev_appserver.py using --api-port')
    parser.add_argument(
        '--secure',
        type=bool,
        default=False,
        help='Whether to use a secure OAuth connection. Default: False')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_flags()  # type: argparse.Namespace

    loggingLevel = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=loggingLevel)

    if args.sdk_root:
        extra_path = os.path.join(args.sdk_root, 'platform/google_appengine')
        logging.info('Adding path %s' % extra_path)
        sys.path.insert(0, extra_path)

    if ('GOOGLE_APPLICATION_CREDENTIALS' not in os.environ
            and args.creds_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = args.creds_path

    main(args)
