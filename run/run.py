#!/usr/bin/python

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

import argparse
import gzip
import json
import platform
import re
import requests
import subprocess
import os

"""
run.py runs WPT and uploads results to Google Cloud Storage.

The dependencies setup and running portion of this script should intentionally
be left small. The brunt of the work should take place in WPT's `wptrun`:
https://github.com/w3c/web-platform-tests/blob/master/tools/wptrun.py

- This script will only write files under BUILD_PATH (defined below)
- One run will write approximately 111MB to the filesystem
- If --upload is specified, it will upload that 111MB of results to Google Storage
- To upload results, you must be logged in with `gcloud` and authorized

By default this script will not upload anything! To do a full run for production:

    ./run/run.py chrome --upload --create-testrun
"""

# TODO: just check that platform-id is valid in browsers.json
VALID_BROWSERS = [
    'chrome',
    'firefox',
]
VALID_OS_NAMES = [
    'linux',
    'macos',
    'windows',
]
# TODO: don't do this, either use wptrun's download feature or parameterize
WPT_PATH = os.path.expanduser('~/gh/w3c/web-platform-tests')
WPTD_PATH = os.path.expanduser('~/gh/GoogleChrome/wptdashboard')
BUILD_PATH =os.path.expanduser('~/wptdbuild')
WPTRUNNER_PATH = '/usr/local/bin/wptrunner'
CHROME_BINARY = '/usr/bin/google-chrome-unstable'
CHROMEDRIVER_BINARY = '/usr/local/bin/chromedriver'
FIREFOX_BINARY = os.path.expanduser('~/Downloads/firefox/firefox')
GECKODRIVER_BINARY = '/usr/local/bin/geckodriver'
FIREFOX_PREFS_ROOT = os.path.expanduser('~/profiles')
WPTD_PROD_HOST = 'https://running-dot-wptdashboard.appspot.com'
GS_RESULTS_BUCKET = 'wptd'


def get_browser_version(browser, browser_binary):
    if browser in ('chrome', 'firefox'):
        output = subprocess.check_output([browser_binary, '--version']).strip()
        version = re.search("[0-9]{1,3}.[0-9]{1,3}", output).group(0)
    else:
        raise

    return version


def get_os_name():
    os_name = platform.system().lower()
    assert os_name in VALID_OS_NAMES
    return os_name


def get_os_version():
    return platform.release()


def get_current_wpt_sha():
    command = ['git', 'rev-parse', 'HEAD']
    sha = subprocess.check_output(command, cwd=WPT_PATH).strip()

    assert len(sha) == 40, 'Invalid SHA: "%s"' % sha
    return sha


def report_to_summary(wpt_report):
    test_files = {}

    for result in wpt_report['results']:
        test_file = result['test']
        assert test_file not in test_files, 'Assumption that each test_file only shows up once broken!'

        if result['status'] in ('OK', 'PASS'):
            test_files[test_file] = [1, 1]
        else:
            test_files[test_file] = [0, 1]

        for subtest in result['subtests']:
            if subtest['status'] == 'PASS':
                test_files[test_file][0] += 1

            test_files[test_file][1] += 1

    return test_files


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('browser',
        help='One of (%s)' % ', '.join(VALID_BROWSERS))
    parser.add_argument('--path',
        help='WPT path to run, if not specified, runs all WPT.',
        default='')
    parser.add_argument('--upload',
        help='Upload results to WPT Dashboard.',
        action='store_true')
    parser.add_argument('--create-testrun',
        help='Creates a new TestRun in the Dashboard. Causes results to be shown immediately.',
        action='store_true')
    args = parser.parse_args()

    assert args.browser in VALID_BROWSERS

    return args


def write_gzip_json(filepath, payload):
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        pass

    with gzip.open(filepath, 'wb') as f:
        json.dump(payload, f)


def main(args):
    print 'Running WPT in %s' % args.browser
    if args.path:
        print 'In path: %s' % args.path
    else:
        print 'Full run! (all tests)'

    if args.upload:
        print 'Setting up storage client'
        from google.cloud import storage
        storage_client = storage.Client(project='wptdashboard')
        bucket = storage_client.get_bucket(GS_RESULTS_BUCKET)

    BROWSER_NAME = args.browser

    if BROWSER_NAME == 'chrome':
        browser_binary = CHROME_BINARY
        webdriver_binary = CHROMEDRIVER_BINARY
    elif BROWSER_NAME == 'firefox':
        browser_binary = FIREFOX_BINARY
        webdriver_binary = GECKODRIVER_BINARY
    else:
        raise

    BROWSER_VERSION = get_browser_version(BROWSER_NAME, browser_binary)
    OS_NAME = get_os_name()
    OS_VERSION = get_os_version()

    print '=================================================='
    print 'Platform information:'
    print 'Browser version: %s' % BROWSER_VERSION
    print 'OS name: %s' % OS_NAME
    print 'OS version: %s' % OS_VERSION

    print '=================================================='
    print 'Setting up WPT checkout'

    print ['git', 'apply', WPTD_PATH]

    wpt_setup_commands = [
        ['git', 'reset', '--hard', 'HEAD'], # Part of keep-wpt-running.patch
        ['git', 'checkout', 'master'],
        ['git', 'pull'],
        ['./manifest', '--work'],
        # Necessary to keep WPT running. jeffcarp has a PR out
        # with this patch: https://github.com/w3c/web-platform-tests/pull/5774
        # however it needs more work.
        ['git', 'apply', '%s/util/keep-wpt-running.patch' % WPTD_PATH],
    ]
    for command in wpt_setup_commands:
        return_code = subprocess.check_call(command, cwd=WPT_PATH)
        assert return_code == 0, 'Got non-0 return code: %d from command %s' % (return_code, command)

    CURRENT_WPT_SHA = get_current_wpt_sha()
    print 'Current WPT SHA: %s' % CURRENT_WPT_SHA

    SHORT_SHA = CURRENT_WPT_SHA[0:10]
    # TODO: use the validated platform ID we pass on the command line
    PLATFORM_ID = '%s-%s-%s-%s' % (BROWSER_NAME, BROWSER_VERSION, OS_NAME, OS_VERSION)

    LOCAL_REPORT_FILEPATH = "%s/wptd-%s-%s-report.log" % (BUILD_PATH, SHORT_SHA, PLATFORM_ID)
    SUMMARY_PATH = '%s/%s-summary.json.gz' % (SHORT_SHA, PLATFORM_ID)
    LOCAL_SUMMARY_GZ_FILEPATH = "%s/%s" % (BUILD_PATH, SUMMARY_PATH)
    GS_RESULTS_FILEPATH_BASE = "%s/%s/%s" % (BUILD_PATH, SHORT_SHA, PLATFORM_ID)
    GS_HTTP_RESULTS_URL = 'https://storage.googleapis.com/%s/%s' % (GS_RESULTS_BUCKET, SUMMARY_PATH)

    print '=================================================='
    print 'Installing wptrunner'
    command = ['pip', 'install', '--user', '-e', 'tools/wptrunner']
    return_code = subprocess.check_call(command, cwd=WPT_PATH)
    assert return_code == 0

    print '=================================================='
    print 'Running WPT'

    command = [
        'xvfb-run',
        WPTRUNNER_PATH,
        '--product', BROWSER_NAME,
        '--binary', browser_binary,
        '--webdriver-binary', webdriver_binary,
        '--meta', WPT_PATH,
        '--tests', WPT_PATH,
        '--log-wptreport', LOCAL_REPORT_FILEPATH,
        '--log-mach=-',
        '--processes=1', # TODO(jeffcarp): investigate if increasing this is stable
    ]
    if BROWSER_NAME == 'firefox':
        command.append('--certutil-binary=certutil')
        command.append('--prefs-root=%s' % FIREFOX_PREFS_ROOT)
    if args.path:
        command.append(args.path)
    print 'COMMAND'
    print ' '.join(command)
    return_code = subprocess.call(command, cwd=WPT_PATH)

    print '=================================================='
    print 'Finished WPT run'
    print 'Return code from wptrunner: %s' % return_code

    with open(LOCAL_REPORT_FILEPATH) as f:
        report = json.load(f)

    assert len(report['results']) > 0, '0 test results, something went wrong, stopping.'

    summary = report_to_summary(report)

    print '=================================================='
    print 'Writing summary.json.gz to local filesystem'
    write_gzip_json(LOCAL_SUMMARY_GZ_FILEPATH, summary)
    print 'Wrote file %s' % LOCAL_SUMMARY_GZ_FILEPATH

    print '=================================================='
    print 'Writing individual result files to local filesystem'
    for result in report['results']:
        test_file = result['test']
        print 'test_file', test_file
        filepath = '%s%s' % (GS_RESULTS_FILEPATH_BASE, test_file)
        print 'filepath', filepath
        write_gzip_json(filepath, result)
        print 'Wrote file %s' % filepath

    if not args.upload:
        print '=================================================='
        print 'Stopping here (pass --upload to upload results to WPTD).'
        return

    print '=================================================='
    print 'Uploading results to gs://%s' % GS_RESULTS_BUCKET
    command = ['gsutil', '-m', '-h', 'Content-Encoding:gzip', 'rsync', '-r', SHORT_SHA, 'gs://wptd/%s' % SHORT_SHA]
    return_code = subprocess.check_call(command, cwd=BUILD_PATH)
    assert return_code == 0
    print 'Successfully uploaded!'
    print 'HTTP summary URL: %s' % GS_HTTP_RESULTS_URL

    if not args.create_testrun:
        print '=================================================='
        print 'Stopping here (pass --create-testrun to create and promote this TestRun).'
        return

    print '=================================================='
    print 'Creating new TestRun in the dashboard...'
    url = '%s/test-runs' % WPTD_PROD_HOST
    requests.post(url, data=json.dumps({
        'browser_name': BROWSER_NAME,
        'browser_version': BROWSER_VERSION,
        'os_name': OS_NAME,
        'os_version': OS_VERSION,
        'revision': SHORT_SHA,
        'results_url': GS_HTTP_RESULTS_URL
    }))


if __name__ == '__main__':
    main(parse_args())
