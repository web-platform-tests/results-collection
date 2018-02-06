#!/usr/bin/python

# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import ConfigParser as configparser
import glob
import gzip
import json
import logging
import platform as host_platform
import re
import requests
import shas
import subprocess
import sys
import traceback
import os

"""
run.py runs WPT and uploads results to Google Cloud Storage.

The dependencies setup and running portion of this script should intentionally
be left small. The brunt of the work should take place in WPT's `wptrun`:
https://github.com/w3c/web-platform-tests/blob/master/tools/wptrun.py

# Running the script

Before you run the script, you need to:

1. Copy run/running.example.ini to run/running.ini
2. Modify the applicable fields of run/running.ini
   (this may also involve installing browsers)
3. Make sure you have the correct secret in run/running.ini
4. Install dependencies with `pip3 install -r requirements.txt`
5. Make sure you have gsutil installed
   (see https://cloud.google.com/storage/docs/gsutil)

The script will only accept platform IDs listed in browsers.json.

By default this script will not upload anything! To run for production:

    ./run/run.py firefox-56.0-linux --upload --create-testrun

# Filesystem and network output

- This script will only write files under config['build_path']
- One run will write approximately 111MB to the filesystem
- If --upload is specified, it will upload that 111MB of results
- To upload results, you must be logged in with `gcloud` and authorized
"""


def main(platform_id, platform, args, config):
    loggingLevel = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=loggingLevel)
    logger = logging.getLogger()

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
        assert len(config['secret']) == 64, (
            'Valid secret required to create TestRun')

    if not platform.get('sauce'):
        if platform['browser_name'] == 'chrome':
            browser_binary = config['chrome_binary']
        elif platform['browser_name'] == 'firefox':
            browser_binary = config['firefox_binary']

        if platform['browser_name'] == 'chrome':
            verify_browser_binary_version(platform, browser_binary)
        verify_os_name(platform)
        verify_or_set_os_version(platform)

    print('Platform information:')
    print('Browser version: %s' % platform['browser_version'])
    print('OS name: %s' % platform['os_name'])
    print('OS version: %s' % platform['os_version'])

    print('==================================================')
    print('Setting up WPT checkout')

    setup_wpt(config)

    print('Patching WPT')
    patch_wpt(config, platform)

    print('Getting WPT commit SHA and Date')
    wpt_sha, wpt_commit_date = get_commit_details(args, config, logger)

    print('WPT SHA: %s' % wpt_sha)
    print('WPT Commit Date: %s' % wpt_commit_date)

    short_wpt_sha = wpt_sha[0:10]

    abs_report_log_path = "%s/wptd-%s-%s-report.log" % (
        config['build_path'], short_wpt_sha, platform_id
    )
    abs_report_chunks_path = "%s/%s/%s-report-chunks" % (
        config['build_path'], short_wpt_sha, platform_id
    )
    mkdirp(abs_report_chunks_path)

    sha_summary_gz_path = '%s/%s-summary.json.gz' % (
        short_wpt_sha, platform_id
    )
    abs_sha_summary_gz_path = "%s/%s" % (
        config['build_path'], sha_summary_gz_path
    )

    gs_results_base_path = "%s/%s/%s" % (
        config['build_path'], short_wpt_sha, platform_id
    )
    gs_results_url = 'https://storage.googleapis.com/%s/%s' % (
        config['gs_results_bucket'], sha_summary_gz_path
    )

    print('==================================================')
    print('Running WPT')

    for this_chunk in range(1, args.total_chunks + 1):
        if platform.get('sauce'):
            if platform['browser_name'] == 'edge':
                sauce_browser_name = 'MicrosoftEdge'
            else:
                sauce_browser_name = platform['browser_name']

            command = [
                './wpt', 'run', 'sauce:%s:%s' % (
                    sauce_browser_name, platform['browser_version']),
                '--sauce-platform=%s' % platform['os_name'],
                '--sauce-key=%s' % config['sauce_key'],
                '--sauce-user=%s' % config['sauce_user'],
                '--sauce-connect-binary=%s' % config['sauce_connect_path'],
                '--sauce-tunnel-id=%s' % config['sauce_tunnel_id'],
                '--no-restart-on-unexpected',
                '--processes=2',
                '--run-by-dir=3',
            ]
            if args.path:
                command.insert(3, args.path)
        else:
            command = [
                'xvfb-run', '--auto-servernum',
                './wpt', 'run',
                platform['browser_name'],
            ]

            if args.path:
                command.insert(5, args.path)
            if platform['browser_name'] == 'chrome':
                command.extend(['--binary', browser_binary])
            if platform['browser_name'] == 'firefox':
                command.extend(['--install-browser', '--yes'])
                command.append('--certutil-binary=certutil')
                # temporary fix to allow WebRTC tests to call getUserMedia
                command.extend([
                    '--setpref', 'media.navigator.streams.fake=true'
                ])

        command.append('--log-mach=-')
        partial_report_filename = '%s/%s-of-%s.json' % (
            abs_report_chunks_path, this_chunk, args.total_chunks
        )
        command.extend(['--log-wptreport', partial_report_filename])
        command.append('--install-fonts')
        command.extend([
            '--this-chunk', str(this_chunk),
            '--total-chunks', str(args.total_chunks)
        ])

        for attempt_number in range(1, args.max_attempts + 1):
            print('Running chunk %s of %s (attempt %s of %s)' % (
                this_chunk, args.total_chunks, attempt_number,
                args.max_attempts
            ))
            return_code = subprocess.call(command, cwd=config['wpt_path'])

            print('Return code from wptrunner: %s' % return_code)

            try:
                with open(partial_report_filename) as f:
                    partial_report = json.load(f)

                result_count = len(partial_report['results'])

                print('Report contains %s results' % result_count)

                if result_count > 0:
                    break
            except Exception:
                print(traceback.format_exc())

    print('==================================================')
    print('Finished WPT run')

    if platform['browser_name'] == 'firefox':
        print('Verifying installed firefox matches platform ID')
        firefox_path = '%s/_venv/firefox/firefox' % config['wpt_path']
        verify_browser_binary_version(platform, firefox_path)

    print('Consolidating results')
    full_report = {'results': []}
    for name in glob.glob('%s/*.json' % abs_report_chunks_path):
        with open(name) as f:
            partial_report = json.load(f)

        full_report['results'].extend(partial_report['results'])

    summary = report_to_summary(full_report)

    print('==================================================')
    print('Writing summary.json.gz to local filesystem')
    write_gzip_json(abs_sha_summary_gz_path, summary)
    print('Wrote file %s' % abs_sha_summary_gz_path)

    print('==================================================')
    print('Writing individual result files to local filesystem')
    for result in full_report['results']:
        test_file = result['test']
        filepath = '%s%s' % (gs_results_base_path, test_file)
        write_gzip_json(filepath, result)
        print('Wrote file %s' % filepath)

    if not args.upload:
        print('==================================================')
        print('Stopping here (pass --upload to upload results to WPTD).')
        return

    print('==================================================')
    print('Uploading results to gs://%s' % config['gs_results_bucket'])
    command = ['gsutil', '-m', '-h', 'Content-Encoding:gzip',
               'rsync', '-r', short_wpt_sha, 'gs://wptd/%s' % short_wpt_sha]
    return_code = subprocess.check_call(command, cwd=config['build_path'])
    assert return_code == 0
    print('Successfully uploaded!')
    print('HTTP summary URL: %s' % gs_results_url)

    if not args.create_testrun:
        print('==================================================')
        print('Stopping here')
        print('pass --create-testrun to create and promote this TestRun).')
        return

    print('==================================================')
    print('Creating new TestRun in the dashboard...')
    url = '%s/api/run' % config['wptd_prod_host']
    response = requests.post(url, params={
            'secret': config['secret']
        },
        data=json.dumps({
            'browser_name': platform['browser_name'],
            'browser_version': platform['browser_version'],
            'commit_date': wpt_commit_date,
            'os_name': platform['os_name'],
            'os_version': platform['os_version'],
            'revision': short_wpt_sha,
            'results_url': gs_results_url
        }
    ))
    if response.status_code == 201:
        print('Run created!')
    else:
        print('There was an issue creating the TestRun.')

    print('Response status code:', response.status_code)
    print('Response text:', response.text)


def setup_wpt(config):
    wpt_setup_commands = [
        ['git', 'reset', '--hard', 'HEAD'],  # For wpt.patch
        ['git', 'checkout', 'master'],
        ['git', 'pull'],
        ['./wpt', 'manifest', '--work'],
    ]
    for command in wpt_setup_commands:
        return_code = subprocess.check_call(command, cwd=config['wpt_path'])
        assert return_code == 0, (
            'Got non-0 return code: '
            '%d from command %s' % (return_code, command))

    return 0


def get_commit_details(mainargs, config, logger):
    wpt_sha = ''
    wpt_date = ''

    if mainargs.wpt_sha:
        wpt_sha = mainargs.wpt_sha
    else:
        sha_finder = shas.SHAFinder(logger)
        wpt_sha = (sha_finder.get_todays_sha(config['wpt_path'])
                   or sha_finder.get_head_sha(config['wpt_path']))

    subprocess.call(['git', 'checkout', wpt_sha], cwd=config['wpt_path'])
    output = subprocess.check_output(
        ['git', 'log', '-1', '--format=%cd', '--date=iso-strict'],
        cwd=config['wpt_path']
    )
    wpt_date = output.decode('UTF-8').strip()

    return wpt_sha, wpt_date


def get_and_validate_platform(platform_id):
    with open('webapp/browsers.json') as f:
        browsers = json.load(f)

    assert platform_id in browsers, 'platform_id not found in browsers.json'
    return browsers[platform_id]


def version_string_to_major_minor(version):
    assert version
    return re.search("[0-9]{1,3}.[0-9]{1,3}", str(version)).group(0)


def verify_browser_binary_version(platform, browser_binary):
    command = [browser_binary, '--version']
    try:
        output = subprocess.check_output(command).decode('UTF-8').strip()
        version = version_string_to_major_minor(output)
        assert version == platform['browser_version'], (
            'Browser binary version does not match desired platform version.\n'
            'Binary location: %s\nBinary version: %s\nPlatform version: %s\n'
            % (browser_binary, version, platform['browser_version']))
    except OSError as e:
        logging.fatal('Error executing %s' % ' '.join(command))
        raise e


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


def report_to_summary(wpt_report):
    test_files = {}

    for result in wpt_report['results']:
        test_file = result['test']
        assert test_file not in test_files, (
            'Assumption that each test_file only shows up once broken!')

        if result['status'] in ('OK', 'PASS'):
            test_files[test_file] = [1, 1]
        else:
            test_files[test_file] = [0, 1]

        for subtest in result['subtests']:
            if subtest['status'] == 'PASS':
                test_files[test_file][0] += 1

            test_files[test_file][1] += 1

    return test_files


# Create all non-existent directories in a specified path
def mkdirp(path):
    try:
        os.makedirs(path)
    except OSError:
        pass


def write_gzip_json(filepath, payload):
    mkdirp(os.path.dirname(filepath))

    with gzip.open(filepath, 'wb') as f:
        payload_str = json.dumps(payload)
        f.write(payload_str)


def verify_gsutil_installed(config):
    assert subprocess.check_output(['which', 'gsutil']), (
        'gsutil required for upload')


def get_config():
    manifest = "run/running.ini"
    config = configparser.ConfigParser()
    if os.path.isfile(manifest):
        config.read(manifest)
    else:
        print("The manifest {0} does not exist.".format(manifest))
        sys.exit()

    expand_keys = [
        'build_path', 'wpt_path', 'wptd_path', 'firefox_binary',
        'sauce_connect_path',
    ]
    # Expand paths, this is for convenience so you can use $HOME
    for key in expand_keys:
        config.set('default',
                   key,
                   os.path.expandvars(config.get('default', key)))
    conf = {}
    for item in config.items('default'):
        k, v = item
        conf[k] = v
    return conf


def patch_wpt(config, platform):
    """Applies util/wpt.patch to WPT.

    The patch is necessary to keep WPT running on long runs.
    jeffcarp has a PR out with this patch:
    https://github.com/w3c/web-platform-tests/pull/5774
    """
    patch_path = '%s/util/wpt.patch' % config['wptd_path']
    with open(patch_path) as f:
        patch = f.read()

    # The --sauce-platform command line arg doesn't
    # accept spaces, but Sauce requires them in the platform name.
    # https://github.com/w3c/web-platform-tests/issues/6852
    patch = patch.replace('__platform_hack__', '%s %s' % (
        platform['os_name'], platform['os_version'])
    )

    p = subprocess.Popen(
        ['git', 'apply', '-'], cwd=config['wpt_path'], stdin=subprocess.PIPE
    )
    p.communicate(input=patch)


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
    parser.add_argument(
        '--log',
        type=str,
        default='INFO',
        help='Log level to output'
    )
    parser.add_argument(
        '--wpt_sha',
        help='https://github.com/w3c/web-platform-tests commit SHA to test.'
    )
    parser.add_argument(
        '--total_chunks',
        help='Total number of chunks to use (forwarded to the `wpt` CLI)',
        type=int,
        default=1
    )
    parser.add_argument(
        '--max_attempts',
        help=('Maximum number of times to re-try running any given failing '
              'chunk'),
        type=int,
        default=3
    )
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    platform = get_and_validate_platform(args.platform_id)
    config = get_config()
    main(args.platform_id, platform, args, config)
