# This replaces run/run.py
import json
import gzip
import os
import requests
import subprocess
import time
import re


# For making instance-internal network requests for metadata.
# See: https://cloud.google.com/compute/docs/storing-retrieving-metadata
METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1'


def main():
    # TODO after --install-browser verify browser
    #      version or change platform ID to correct browser version
    #      This can be done by running `wpt install firefox` and then verifying
    # TODO report OS version when creating TestRun
    # TODO check out correct WPT revision
    # TODO convert these back into command line args. They're currently
    #      env vars due to an earlier change. They should be converted back.
    # TODO break this file up into smaller, unit tested modules.
    # TODO document how we use metadata
    args = {
        'prod_run': bool(os.environ.get('PROD_RUN', False)),
        'prod_wet_run': bool(os.environ.get('PROD_WET_RUN', False)),
        'SHA': os.environ.get('WPT_SHA'),
        'sauce_from_metadata': bool(os.environ.get('SAUCE_FROM_METADATA')),
        'sauce_key': os.environ.get('SAUCE_KEY', ''),
        'sauce_user': os.environ.get('SAUCE_USER', ''),
        'jenkins_job_name': os.environ.get('JOB_NAME'),
        'wpt_path': os.environ.get('WPT_PATH'),
        'wptd_path': (os.environ.get('WPTD_PATH') or
                      '%s/wptdashboard' % (os.environ.get('HOME'))),
        'output_path': (os.environ.get('WPTD_OUT_PATH') or
                        '%s/wptdout' % (os.environ.get('HOME'))),

        # Passing RUN_PATH will run a specific path in WPT (e.g. html)
        'run_path': os.environ.get('RUN_PATH', ''),
    }

    # Arg validation
    assert args['wpt_path'], '`WPT_PATH` env var required.'
    assert not args['wpt_path'].endswith('/'), '`WPT_PATH` cannot end with /.'
    assert len(args['SHA']) == 10, '`WPT_SHA` env var required.'

    if args['prod_run'] or args['prod_wet_run']:
        print 'Fetching upload_secret from GCE Metadata...'

        url = '%s/project/attributes/upload_secret' % METADATA_URL
        res = requests.get(url, headers={'Metadata-Flavor': 'Google'})
        args['upload_secret'] = res.text
        assert len(args['upload_secret']) == 64, (
            'Metadata `upload_secret` must exist for prod runs.')

    platform_id, platform = get_and_validate_platform(args['wptd_path'])

    PROD_HOST = 'https://wptdashboard.appspot.com'
    GS_RESULTS_BUCKET = 'wptd'
    LOCAL_LOG_FILEPATH = '%s/wptd-testrun.log' % args['output_path']
    LOCAL_REPORT_FILEPATH = "%s/wptd-%s-%s-report.log" % (
        args['output_path'], args['SHA'], platform_id
    )
    SUMMARY_PATH = '%s/%s-summary.json.gz' % (args['SHA'], platform_id)
    LOCAL_SUMMARY_GZ_FILEPATH = "%s/%s" % (args['output_path'], SUMMARY_PATH)
    GS_RESULTS_FILEPATH_BASE = "%s/%s/%s" % (
        args['output_path'], args['SHA'], platform_id
    )
    GS_HTTP_RESULTS_URL = 'https://storage.googleapis.com/%s/%s' % (
        GS_RESULTS_BUCKET, SUMMARY_PATH
    )

    SUMMARY_FILENAME = '%s-%s-summary.json.gz' % (args['SHA'], platform_id)
    SUMMARY_HTTP_URL = 'https://storage.googleapis.com/%s/%s' % (
        GS_RESULTS_BUCKET, SUMMARY_FILENAME
    )

    if platform.get('sauce'):
        if args['sauce_from_metadata']:
            print 'Fetching Sauce creds from GCE metadata...'

            for key in ('sauce_user', 'sauce_key'):
                url = '%s/project/attributes/%s' % (METADATA_URL, key)
                res = requests.get(url, headers={'Metadata-Flavor': 'Google'})
                args[key] = res.text
                assert args[key], 'Metadata key %s is empty.' % key

        assert args['sauce_key'], 'SAUCE_KEY env var required'
        assert args['sauce_user'], 'SAUCE_USER env var required'
        SAUCE_TUNNEL_ID = '%s_%s' % (platform_id, int(time.time()))

    assert len(args['SHA']) == 10, 'SHA must a WPT SHA[:10]'

    # Hack because Sauce expects a different name
    # Maybe just change it in browsers.json?
    if platform['browser_name'] == 'edge':
        sauce_browser_name = 'MicrosoftEdge'
    else:
        sauce_browser_name = platform['browser_name']
    product = 'sauce:%s:%s' % (sauce_browser_name, platform['browser_version'])

    patch_wpt(args['wptd_path'], args['wpt_path'], platform)

    if platform.get('sauce'):
        command = [
            './wpt', 'run', product,
            '--sauce-platform=%s' % platform['os_name'],
            '--sauce-key=%s' % args['sauce_key'],
            '--sauce-user=%s' % args['sauce_user'],
            '--sauce-tunnel-id=%s' % SAUCE_TUNNEL_ID,
            '--no-restart-on-unexpected',
            '--processes=2',
            '--run-by-dir=3',
            '--log-mach=-',
            '--log-wptreport=%s' % LOCAL_REPORT_FILEPATH,
            '--install-fonts'
        ]
        if args['run_path']:
            command.insert(3, args['run_path'])
    else:
        command = [
            'xvfb-run', '--auto-servernum',
            './wpt', 'run',
            platform['browser_name'],
            '--install-fonts',
            '--install-browser',
            '--yes',
            '--log-mach=%s' % LOCAL_LOG_FILEPATH,
            '--log-wptreport=%s' % LOCAL_REPORT_FILEPATH,
        ],
        if platform['browser_name'] == 'firefox':
          # for webrtc
          command.extend(['--setpref', 'media.navigator.streams.fake=true'])
        if args['run_path']:
            command.insert(5, args['run_path'])

    return_code = subprocess.call(command, cwd=args['wpt_path'])

    print('==================================================')
    print('Finished WPT run')
    print('Return code from wptrunner: %s' % return_code)

    with open(LOCAL_REPORT_FILEPATH) as f:
        report = json.load(f)

    assert len(report['results']) > 0, (
        '0 test results, something went wrong, stopping.')

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

    if not (args['prod_run'] or args['prod_wet_run']):
        print('==================================================')
        print('Stopping here (set PROD_RUN env var to upload results).')
        return

    print('==================================================')
    print('Uploading results to gs://%s' % GS_RESULTS_BUCKET)

    # TODO(#80): change this from rsync to cp
    command = ['gsutil', '-m', '-h', 'Content-Encoding:gzip',
               'rsync', '-r', args['SHA'], 'gs://wptd/%s' % args['SHA']]
    return_code = subprocess.check_call(command, cwd=args['output_path'])
    assert return_code == 0, 'gsutil rsync return code was not 0!'
    print('Successfully uploaded!')
    print('HTTP summary URL: %s' % GS_HTTP_RESULTS_URL)

    print('==================================================')
    print('Creating new TestRun in the dashboard...')
    url = '%s/api/run' % PROD_HOST

    if args['prod_run']:
        final_browser_name = platform['browser_name']
    else:
        # The PROD_WET_RUN is identical to PROD_RUN, however the
        # browser name it creates will be prefixed by eval-,
        # causing it to not show up in the dashboard.
        final_browser_name = 'eval-%s' % platform['browser_name']

    response = requests.post(url, params={
            'secret': args['upload_secret']
        },
        data=json.dumps({
            'browser_name': final_browser_name,
            'browser_version': platform['browser_version'],
            'os_name': platform['os_name'],
            'os_version': platform['os_version'],
            'revision': args['SHA'],
            'results_url': GS_HTTP_RESULTS_URL
        }
    ))
    if response.status_code == 201:
        print('Run created!')
    else:
        print('There was an issue creating the TestRun.')

    print('Response status code:', response.status_code)
    print('Response text:', response.text)


def patch_wpt(wptd_path, wpt_path, platform):
    """Applies util/wpt.patch to WPT.

    The patch is necessary to keep WPT running on long runs.
    jeffcarp has a PR out with this patch:
    https://github.com/w3c/web-platform-tests/pull/5774
    """
    with open('%s/util/wpt.patch' % wptd_path) as f:
        patch = f.read()

    # The --sauce-platform command line arg doesn't
    # accept spaces, but Sauce requires them in the platform name.
    # https://github.com/w3c/web-platform-tests/issues/6852
    patch = patch.replace('__platform_hack__', '%s %s' % (
        platform['os_name'], platform['os_version'])
    )

    p = subprocess.Popen(
        ['git', 'apply', '-'], cwd=wpt_path, stdin=subprocess.PIPE
    )
    p.communicate(input=patch)


def get_and_validate_platform(wptd_path):
    """Validates testing platform ID against currently tested platforms."""
    with open('%s/browsers.json' % wptd_path) as f:
        browsers = json.load(f)

    platform_id = os.environ['PLATFORM_ID']
    assert platform_id, 'PLATFORM_ID env var required (keys in browsers.json)'
    assert platform_id in browsers, 'PLATFORM_ID not found in browsers.json'
    return platform_id, browsers.get(platform_id)


def report_to_summary(wpt_report):
    """Parses a wptreport log object into a file-wise summary."""
    test_files = {}

    for result in wpt_report['results']:
        test_file = result['test']

        # We expect wpt_report to output only one entry per test.
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


def write_gzip_json(filepath, payload):
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        pass

    with gzip.open(filepath, 'wb') as f:
        payload_str = json.dumps(payload)
        f.write(payload_str)


if __name__ == '__main__':
    main()
