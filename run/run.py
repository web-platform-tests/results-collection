#!/usr/bin/python

# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import division

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
import shutil
import subprocess
import tempfile
import threading
import traceback
import os

from report import Report, InsufficientData

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
    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level=loggingLevel, format=log_format)
    logger = logging.getLogger(' ')

    logger.info('PLATFORM_ID: %s', platform_id)
    logger.info('PLATFORM INFO: %s', platform)

    if args.path:
        logger.info('Running tests in path: %s', args.path)
    else:
        logger.info('Running all tests!')

    if args.upload:
        logger.info('Setting up storage client')
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

    logger.info('Platform information:')
    logger.info('Browser version: %s', platform['browser_version'])
    logger.info('OS name: %s', platform['os_name'])
    logger.info('OS version: %s', platform['os_version'])

    logger.info('Setting up WPT checkout')

    setup_wpt(config, logger)

    logger.info('Getting WPT commit SHA and Date')
    wpt_sha, wpt_commit_date = get_commit_details(args, config, logger)

    logger.info('WPT SHA: %s', wpt_sha)
    logger.info('WPT Commit Date: %s', wpt_commit_date)

    short_wpt_sha = wpt_sha[0:10]

    abs_report_log_path = "%s/wptd-%s-%s-report.log" % (
        config['build_path'], short_wpt_sha, platform_id
    )
    abs_report_chunks_path = "%s/%s/%s-report-chunks" % (
        config['build_path'], short_wpt_sha, platform_id
    )
    abs_current_chunk_path = os.path.join(
        abs_report_chunks_path, 'current.json'
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

    logger.info('Running WPT')

    report = Report(args.total_chunks, abs_report_chunks_path)
    missing_tests = set()
    expected_test_count = 0

    for this_chunk in range(1, args.total_chunks + 1):
        if platform.get('sauce'):
            if platform['browser_name'] == 'edge':
                sauce_browser_name = 'MicrosoftEdge'
            else:
                sauce_browser_name = platform['browser_name']

            command = [
                './wpt', 'run', 'sauce:%s:%s' % (
                    sauce_browser_name, platform['browser_version']),
                '--sauce-platform=%s %s' % (
                    platform['os_name'], platform['os_version']),
                '--sauce-key=%s' % config['sauce_key'],
                '--sauce-user=%s' % config['sauce_user'],
                '--sauce-connect-binary=%s' % config['sauce_connect_binary'],
                '--sauce-tunnel-id=%s' % config['sauce_tunnel_id'],
                '--no-restart-on-unexpected',
                '--processes=2',
                '--run-by-dir=3',
            ]
            if args.path:
                command.insert(3, args.path)
        else:
            command = [
                './wpt', 'run',
                platform['browser_name'],
            ]

            if args.path:
                command.insert(5, args.path)
            if platform['browser_name'] == 'chrome':
                command.extend(['--binary', browser_binary])

                # temporary fix to allow WebRTC tests to call getUserMedia
                command.extend(
                    ['--binary-arg=--use-fake-ui-for-media-stream',
                     '--binary-arg=--use-fake-device-for-media-stream'])
            if platform['browser_name'] == 'firefox':
                command.extend(['--binary', browser_binary])
                # we no longer want to download a firefox binary
                command.append('--yes')
                # this actually refers to 'say yes to everything'
                # and not installing a browser, as previously written
                command.append('--certutil-binary=certutil')
                # temporary fix to allow WebRTC tests to call getUserMedia
                command.extend([
                    '--setpref', 'media.navigator.streams.fake=true'
                ])

        command.append('--log-mach=-')
        raw_log_filename = tempfile.mkstemp('-wptdashboard')[1]
        command.extend(['--log-raw', raw_log_filename])

        command.extend(['--log-wptreport', abs_current_chunk_path])
        command.append('--install-fonts')
        command.extend([
            '--this-chunk', str(this_chunk),
            '--total-chunks', str(args.total_chunks)
        ])

        for attempt_number in range(1, args.max_attempts + 1):
            logger.info(
                'Running chunk %s of %s (attempt %s of %s)', this_chunk,
                args.total_chunks, attempt_number, args.max_attempts
            )

            # In the event of a failed attempt, previously-created files will
            # still be available on disk. Remove these to guard against errors
            # where the next attempt fails to write new results.
            for name in (abs_current_chunk_path, raw_log_filename):
                try:
                    os.remove(name)
                except OSError:
                    pass

            proc = subprocess.Popen(
                command, cwd=config['wpt_path'], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            log_streams('wpt', proc, logger)

            proc.wait()

            logger.info('Return code from wptrunner: %s', proc.returncode)

            expected_tests = get_expected_tests(raw_log_filename)
            chunk_test_count = len(expected_tests)

            logger.info('%s tests defined in chunk', chunk_test_count)

            expected_test_count += chunk_test_count

            try:
                data = report.load_chunk(this_chunk, abs_current_chunk_path)

                logger.info('Report contains %s results', len(data['results']))

                actual_tests = [test['test'] for test in data['results']]
                missing_tests.update(set(expected_tests) - set(actual_tests))

                break
            except InsufficientData:
                pass
        else:
            logger.info(
                'No results found after %s attempts. Giving up.',
                args.max_attempts
            )

        os.remove(raw_log_filename)

    logger.info('Finished WPT run')

    if platform['browser_name'] == 'firefox':
        logger.info('Verifying installed firefox matches platform ID')
        firefox_path = config['firefox_binary']
        verify_browser_binary_version(platform, firefox_path)

    logger.info('Creating summary of results')
    try:
        summary = report.summarize()

        actual_test_count = len(summary.keys())
        actual_percentage = actual_test_count / expected_test_count

        missing_tests_count = len(missing_tests)
        logger.info('%s missing tests', missing_tests_count)
        for test_name in missing_tests:
            logger.info('- %s', test_name)

        if actual_percentage < args.partial_threshold / 100:
            raise InsufficientData('%s of %s is below threshold of %s%%' % (
                actual_test_count, expected_test_count, args.partial_threshold)
            )
    except InsufficientData as exc:
        logging.fatal('Insufficient report data (%s). Stopping.', exc)
        exit(1)

    logger.info('Writing summary.json.gz to local filesystem')
    write_gzip_json(abs_sha_summary_gz_path, summary)
    logger.info('Wrote file %s', abs_sha_summary_gz_path)

    logger.info('Writing individual result files to local filesystem')
    for result in report.each_result():
        test_file = result['test']
        filepath = '%s%s' % (gs_results_base_path, test_file)
        write_gzip_json(filepath, result)
        logger.info('Wrote file %s', filepath)

    logger.info('Removing "chunk" results')
    shutil.rmtree(abs_report_chunks_path)

    if not args.upload:
        logger.info('Stopping here (pass --upload to upload results to WPTD).')
        return

    logger.info('Uploading results to gs://%s', config['gs_results_bucket'])
    command = ['gsutil', '-m', '-h', 'Content-Encoding:gzip',
               'rsync', '-r', short_wpt_sha, 'gs://wptd/%s' % short_wpt_sha]
    return_code = subprocess.check_call(command, cwd=config['build_path'])
    assert return_code == 0
    logger.info('Successfully uploaded!')
    logger.info('HTTP summary URL: %s', gs_results_url)

    if not args.create_testrun:
        logger.info('Stopping here')
        logger.info(
            'Pass --create-testrun to create and promote this TestRun.'
        )
        return

    logger.info('Creating new TestRun in the dashboard...')
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
        logger.info('Run created!')
    else:
        logger.info('There was an issue creating the TestRun.')

    logger.info('Response status code: %s', response.status_code)
    logger.info('Response text: %s', response.text)


def log_streams(command_name, proc, logger):
    def target(cmd_name, stream_name, stream, logger):
        prefix = '%s:%s ' % (cmd_name, stream_name)

        with stream:
            for line in iter(stream.readline, b''):
                logger.debug(prefix + line.rstrip())

    threading.Thread(
        target=target, args=(command_name, 'stdout', proc.stdout, logger)
    ).start()

    threading.Thread(
        target=target, args=(command_name, 'stderr', proc.stderr, logger)
    ).start()


def setup_wpt(config, logger):
    wpt_setup_commands = [
        ['git', 'checkout', 'master'],
        ['git', 'pull'],
        ['./wpt', 'manifest', '--work'],
    ]
    for command in wpt_setup_commands:
        proc = subprocess.Popen(
            command, cwd=config['wpt_path'], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        logger.info('Running command: %s', ' '.join(command))
        log_streams(command[0], proc, logger)

        proc.wait()

        assert proc.returncode == 0, (
            'Got non-0 return code: '
            '%d from command %s' % (proc.returncode, command))

    return 0


def get_expected_tests(filename):
    '''Retrieve a list of strings which define all tests available in a given
    Web Platform Test repository. This number is distinct from the number of
    test files due to the presence of "multi-global" tests.'''

    with open(filename) as handle:
        for line in handle:
            try:
                data = json.loads(line)
            except ValueError:
                continue

            if data.get('action') != 'suite_start':
                continue

            return data.get('tests').get('default')

    return []


def get_commit_details(mainargs, config, logger):
    wpt_sha = ''
    wpt_date = ''

    if mainargs.wpt_sha:
        wpt_sha = mainargs.wpt_sha
    else:
        sha_finder = shas.SHAFinder(logger)
        wpt_sha = (sha_finder.get_todays_sha(config['wpt_path'])
                   or sha_finder.get_head_sha(config['wpt_path']))

    proc = subprocess.Popen(
        ['git', 'checkout', wpt_sha], cwd=config['wpt_path'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    log_streams('git', proc, logger)

    proc.wait()

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
    assert os.path.isfile(manifest), (
        'The manifest %s does not exist.' % manifest
    )

    config.read(manifest)

    expand_keys = [
        'build_path', 'chrome_binary', 'wpt_path', 'wptd_path',
        'firefox_binary', 'sauce_connect_binary',
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


def parse_percent(string):
    parsed = int(string)

    if parsed < 0 or parsed > 100:
        raise ValueError('Percent value must be between 0 and 100')

    return parsed


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
        '--total-chunks',
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

    parser.add_argument(
        '--partial-threshold',
        help=('Save reports for datasets that omit results for some tests. '
              'This must be an integer between 1 and 100 describing the '
              'minimum percentage of results that must be present for reports '
              'to be saved. Defaults to 0 (i.e. empty results allowed.)'),
        type=parse_percent,
        action='store',
        default=0
    )
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    platform = get_and_validate_platform(args.platform_id)
    config = get_config()
    main(args.platform_id, platform, args, config)
