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

import argparse
import configparser
import gzip
import json
import platform as host_platform
import re
import requests
import subprocess
import sys
import os

"""
run.py runs WPT and uploads results to Google Cloud Storage.

The dependencies setup and running portion of this script should intentionally
be left small. The brunt of the work should take place in WPT's `wptrun`:
https://github.com/w3c/web-platform-tests/blob/master/tools/wptrun.py

# Running the script

Before you run the script, you need to:

1. Copy run/running.example.ini to run/running.ini
2. Modify the applicable fields of run/running.ini (this may also involve installing browsers)
3. Make sure you have the correct secret in run/running.ini
4. Install dependencies with `pip3 install -r requirements.txt`
5. Make sure you have gsutil installed (see https://cloud.google.com/storage/docs/gsutil)

The script will only accept platform IDs listed in browsers.json.

By default this script will not upload anything! To do a full run for production:

    ./run/run.py firefox-56.0-linux --upload --create-testrun

# Filesystem and network output

- This script will only write files under config['build_path']
- One run will write approximately 111MB to the filesystem
- If --upload is specified, it will upload that 111MB of results to Google Storage
- To upload results, you must be logged in with `gcloud` and authorized
"""

def main(platform_id, platform, args, config):
    assert sys.version_info.major == 3, 'This script requires Python 3.'

    print('PLATFORM_ID:', platform_id)
    print('PLATFORM INFO:', platform)

    if args.path:
        print('Running tests in path: %s' % args.path)
    else:
        print('Running all tests!')

    if args.upload:
        print('Setting up storage client')
        from google.cloud import storage
        storage_client = storage.Client(project='wptdashboard')
        bucket = storage_client.get_bucket(config['gs_results_bucket'])
        verify_gsutil_installed(config)

    if args.create_testrun:
        assert len(config['secret']) == 64, 'Valid secret required to create TestRun'

    if platform['browser_name'] == 'chrome':
        browser_binary = config['chrome_binary']
        webdriver_binary = config['chromedriver_binary']
    elif platform['browser_name'] == 'firefox':
        browser_binary = config['firefox_binary']
        webdriver_binary = config['geckodriver_binary']
    else:
        raise

    verify_browser_binary_version(platform, browser_binary)
    verify_os_name(platform)
    verify_or_set_os_version(platform)

    print('Platform information:')
    print('Browser version: %s' % platform['browser_version'])
    print('OS name: %s' % platform['os_name'])
    print('OS version: %s' % platform['os_version'])

    print('==================================================')
    print('Setting up WPT checkout')

    wpt_setup_commands = [
        ['git', 'reset', '--hard', 'HEAD'], # Needed b/c of keep-wpt-running.patch
        ['git', 'checkout', 'master'],
        ['git', 'pull'],
        ['./manifest', '--work'],
        # Necessary to keep WPT running on long runs. jeffcarp has a PR out
        # with this patch: https://github.com/w3c/web-platform-tests/pull/5774
        # however it needs more work.
        ['git', 'apply', '%s/util/keep-wpt-running.patch' % config['wptd_path']],
    ]
    for command in wpt_setup_commands:
        return_code = subprocess.check_call(command, cwd=config['wpt_path'])
        assert return_code == 0, 'Got non-0 return code: %d from command %s' % (return_code, command)

    # TODO(#40): modify this to test against the first SHA of the day
    CURRENT_WPT_SHA = get_current_wpt_sha(config)
    print('Current WPT SHA: %s' % CURRENT_WPT_SHA)

    SHORT_SHA = CURRENT_WPT_SHA[0:10]

    LOCAL_REPORT_FILEPATH = "%s/wptd-%s-%s-report.log" % (config['build_path'], SHORT_SHA, platform_id)
    SUMMARY_PATH = '%s/%s-summary.json.gz' % (SHORT_SHA, platform_id)
    LOCAL_SUMMARY_GZ_FILEPATH = "%s/%s" % (config['build_path'], SUMMARY_PATH)
    GS_RESULTS_FILEPATH_BASE = "%s/%s/%s" % (config['build_path'], SHORT_SHA, platform_id)
    GS_HTTP_RESULTS_URL = 'https://storage.googleapis.com/%s/%s' % (config['gs_results_bucket'], SUMMARY_PATH)

    if config.getboolean('install_wptrunner'):
        print('==================================================')
        print('Installing wptrunner')
        command = ['pip', 'install', '--user', '-e', 'tools/wptrunner']
        return_code = subprocess.check_call(command, cwd=config['wpt_path'])
        assert return_code == 0

    print('==================================================')
    print('Running WPT')

    command = [
        'xvfb-run',
        config['wptrunner_path'],
        '--product', platform['browser_name'],
        '--binary', browser_binary,
        '--webdriver-binary', webdriver_binary,
        '--meta', config['wpt_path'],
        '--tests', config['wpt_path'],
        '--log-wptreport', LOCAL_REPORT_FILEPATH,
        '--log-mach=-',
        '--processes=1', # TODO(jeffcarp): investigate if increasing this is stable
    ]
    if platform['browser_name'] == 'firefox':
        command.append('--certutil-binary=certutil')
        command.append('--prefs-root=%s' % config['firefox_prefs_root'])
    if args.path:
        command.append(args.path)

    return_code = subprocess.call(command, cwd=config['wpt_path'])

    print('==================================================')
    print('Finished WPT run')
    print('Return code from wptrunner: %s' % return_code)

    with open(LOCAL_REPORT_FILEPATH) as f:
        report = json.load(f)

    assert len(report['results']) > 0, '0 test results, something went wrong, stopping.'

    summary = report_to_summary(report)

    print('==================================================')
    print('Writing summary.json.gz to local filesystem')
    write_gzip_json(LOCAL_SUMMARY_GZ_FILEPATH, summary)
    print('Wrote file %s' % LOCAL_SUMMARY_GZ_FILEPATH)

    print('==================================================')
    print('Writing individual result files to local filesystem')
    for result in report['results']:
        test_file = result['test']
        filepath = '%s%s' % (GS_RESULTS_FILEPATH_BASE, test_file)
        write_gzip_json(filepath, result)
        print('Wrote file %s' % filepath)

    if not args.upload:
        print('==================================================')
        print('Stopping here (pass --upload to upload results to WPTD).')
        return

    print('==================================================')
    print('Uploading results to gs://%s' % config['gs_results_bucket'])
    command = ['gsutil', '-m', '-h', 'Content-Encoding:gzip', 'rsync', '-r', SHORT_SHA, 'gs://wptd/%s' % SHORT_SHA]
    return_code = subprocess.check_call(command, cwd=config['build_path'])
    assert return_code == 0
    print('Successfully uploaded!')
    print('HTTP summary URL: %s' % GS_HTTP_RESULTS_URL)

    if not args.create_testrun:
        print('==================================================')
        print('Stopping here (pass --create-testrun to create and promote this TestRun).')
        return

    print('==================================================')
    print('Creating new TestRun in the dashboard...')
    url = '%s/test-runs' % config['wptd_prod_host']
    response = requests.post(url, params={
            'secret': config['secret']
        },
        data=json.dumps({
            'browser_name': platform['browser_name'],
            'browser_version': platform['browser_version'],
            'os_name': platform['os_name'],
            'os_version': platform['os_version'],
            'revision': SHORT_SHA,
            'results_url': GS_HTTP_RESULTS_URL
        }
    ))
    if response.status_code == 201:
        print('Run created!')
    else:
        print('There was an issue creating the TestRun.')

    print('Response status code:', response.status_code)
    print('Response text:', response.text)


def get_and_validate_platform(platform_id):
    with open('browsers.json') as f:
        browsers = json.load(f)

    assert platform_id in browsers, 'platform_id not found in browsers.json'
    return browsers[platform_id]


def version_string_to_major_minor(version):
    return re.search("[0-9]{1,3}.[0-9]{1,3}", str(version)).group(0)


def verify_browser_binary_version(platform, browser_binary):
    if platform['browser_name'] not in ('chrome', 'firefox'):
        return

    output = subprocess.check_output([browser_binary, '--version']).decode('UTF-8').strip()
    version = version_string_to_major_minor(output)
    assert version == platform['browser_version'], (
        'Browser binary version does not match desired platform version.\n'
        'Binary location: %s\nBinary version: %s\nPlatform version: %s\n'
        % (browser_binary, version, browser['browser_version']))


def verify_os_name(platform):
    os_name = host_platform.system().lower()
    assert os_name == platform['os_name'], (
        'Host OS name does not match platform os_name.\n'
        'Host OS name: %s\nPlatform os_name: %s'
        % (os_name, platform['os_name']))


def verify_or_set_os_version(platform):
    os_version = version_string_to_major_minor(host_platform.release())

    if platform['os_version'] == '*':
        platform['os_version'] = os_version
        return

    assert os_version == platform['os_version'], (
        'Host OS version does not match platform os_version.\n'
        'Host OS version: %s\nPlatform os_version: %s'
        % (os_version, platform['os_version']))


def get_current_wpt_sha(config):
    command = ['git', 'rev-parse', 'HEAD']
    sha = subprocess.check_output(command, cwd=config['wpt_path']).decode('UTF-8').strip()

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


def write_gzip_json(filepath, payload):
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        pass

    with gzip.open(filepath, 'wb') as f:
        payload_str = json.dumps(payload)
        f.write(bytes(payload_str, 'UTF-8'))


def verify_gsutil_installed(config):
    assert subprocess.check_output(['which', 'gsutil']), 'gsutil required for upload'


def get_config():
    config = configparser.ConfigParser()
    config.read('run/running.ini')

    # Expand paths, this is for convenience so you can use $HOME
    for key in ['build_path', 'wpt_path', 'wptd_path', 'firefox_binary', 'firefox_prefs_root']:
        config.set('default', key, os.path.expandvars(config['default'][key]))

    return config['default']


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('platform_id',
        help='A platform ID, specified as keys in browsers.json.')
    parser.add_argument('--path',
        help='WPT path to run. If not specified, runs all WPT.',
        default='')
    parser.add_argument('--upload',
        help='Upload results to Google Storage.',
        action='store_true')
    parser.add_argument('--create-testrun',
        help=('Creates a new TestRun in the Dashboard. '
              'Results from this run will be automatically '
              'promoted if "initially_loaded" is true for the '
              'browser in browsers.json.'),
        action='store_true')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    platform = get_and_validate_platform(args.platform_id)
    config = get_config()
    main(args.platform_id, platform, args, config)
