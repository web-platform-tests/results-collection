import gzip
import json
import os
import requests
import subprocess
import time


# TODO after --install-browser verify browser
#      version or change platform ID to correct browser version
#      This can be done by running `wpt install firefox` and then verifying
# TODO report OS version when creating TestRun
# TODO check out correct WPT revision
# TODO convert these back into command line args. They're currently
#      env vars due to an earlier change. They should be converted back.
# TODO break this file up into smaller, unit tested modules.
# TODO document how we use metadata
class Runner(object):
    ASSERT_WPT_PATH = (
        'Runner.wpt_path required. (Default: `WPT_PATH` env var.)'
    )
    ASSERT_WPT_PATH_FMT = 'Runner.wpt_path cannot end with /. %s' % (
        '(Default: `WPT_PATH` env var.)',
    )
    ASSERT_SHA_LEN = 'Runner.sha required. (Default: `WPT_SHA` env var.)'

    def __init__(
        self,

        # For making instance-internal network requests for metadata.
        # See:
        # https://cloud.google.com/compute/docs/storing-retrieving-metadata
        metadata_url=None,
        prod_host=None,
        gs_results_bucket=None,
        prod_run=False,
        prod_wet_run=False,
        sha=None,
        sauce_from_metadata=False,
        sauce_key=None,
        sauce_user=None,
        sauce_tunnel_id=None,
        wpt_path=None,
        wptd_path=None,
        output_path=None,
        # Passing RUN_PATH will run a specific path in WPT (e.g. html)
        run_path=None,
        upload_secret=None,
        platform_id=None,
        platform=None,
        local_log_filepath=None,
        local_report_filepath=None,
        summary_path=None,
        local_summary_gz_filepath=None,
        gs_results_filepath_base=None,
        gs_http_results_url=None,
        summary_filename=None,
        summary_http_url=None,
    ):
        self.metadata_url = metadata_url
        self.prod_host = prod_host,
        self.gs_results_bucket = gs_results_bucket,
        self.prod_run = prod_run
        self.prod_wet_run = prod_wet_run
        self.sha = sha
        self.sauce_from_metadata = sauce_from_metadata
        self.sauce_key = sauce_key
        self.sauce_user = sauce_user
        self.sauce_tunnel_id = sauce_tunnel_id
        self.wpt_path = wpt_path
        self.wptd_path = wptd_path
        self.output_path = output_path
        self.run_path = run_path

        self.upload_secret = upload_secret

        self.platform_id = platform_id
        self.platform = platform

        self.local_log_filepath = local_log_filepath or (
            '%s/wptd-testrun.log' % self.output_path
        )
        self.local_report_filepath = local_report_filepath or (
            '%s/wptd-%s-%s-report.log' % (
                self.output_path, self.sha, self.platform_id
            )
        )
        self.summary_path = summary_path or '%s/%s-summary.json.gz' % (
            self.sha, self.platform_id,
        )
        self.local_summary_gz_filepath = local_summary_gz_filepath or (
            '%s/%s' % (
                self.output_path, self.summary_path,
            )
        )
        self.gs_results_filepath_base = gs_results_filepath_base or (
            '%s/%s/%s' % (
                self.output_path, self.sha, self.platform_id,
            )
        )
        self.gs_http_results_url = gs_http_results_url or (
            'https://storage.googleapis.com/%s/%s' % (
                self.gs_results_bucket, self.summary_path,
            )
        )

        self.summary_filename = summary_filename or '%s-%s-summary.json.gz' % (
            self.sha, self.platform_id,
        )
        self.summary_http_url = summary_http_url or (
            'https://storage.googleapis.com/%s/%s' % (
                self.gs_results_bucket, self.summary_filename,
            )
        )

    def run(self):
        self.validate()
        if self.will_upload():
            self.prep_for_upload()
        if self.run_is_remote():
            self.setup_remote_browser()

        self.patch_wpt(self.wptd_path, self.wpt_path, self.platform)

        if self.run_is_remote():
            return_code = self.do_run_remote()
        else:
            return_code = self.do_run_local()

        print('==================================================')
        print('Finished WPT run')
        print('Return code from wptrunner: %s' % return_code)

        report = self.load_local_report()
        summary = self.report_to_summary(report)

        print('==================================================')
        print('Writing summary.json.gz to local filesystem')
        self.write_gzip_json(self.local_summary_gz_filepath, summary)
        print('Wrote file %s' % self.local_summary_gz_filepath)

        print('==================================================')
        print('Writing individual result files to local filesystem')
        self.write_result_files(report)

        if not self.will_upload():
            print('==================================================')
            print('Stopping here (Runner.will_upload() False).')
            print('Run complete.')
            return

        print('==================================================')
        print('Uploading results to gs://%s' % self.gs_results_bucket)
        self.upload_results()
        print('Successfully uploaded!')
        print('HTTP summary URL: %s' % self.gs_http_results_url)

        print('==================================================')
        print('Creating new TestRun in the dashboard...')
        response = self.upload_run()
        if response.status_code == 201:
            print('Run created!')
        else:
            print('There was an issue creating the TestRun.')

        print('Response status code:', response.status_code)
        print('Response text:', response.text)

        print('==================================================')
        print('Run complete.')

    def validate(self):
        assert self.wpt_path, Runner.ASSERT_WPT_PATH
        assert not self.wpt_path.endswith('/'), Runner.ASSERT_WPT_PATH_FMT
        assert len(self.sha) == 10, Runner.ASSERT_SHA_LEN
        if not (self.platform_id and self.platform):
            self.platform_id, self.platform = self.get_and_validate_platform(
                self.wptd_path,
            )

        if self.platform.get('sauce'):
            assert self.sauce_key and self.sauce_user, Runner.ASSERT_SAUCE_DATA

    def get_and_validate_platform(self, wptd_path):
        """Validates testing platform ID against currently tested platforms."""
        with open('%s/browsers.json' % wptd_path) as f:
            browsers = json.load(f)

        self.platform_id = os.environ['PLATFORM_ID']
        assert self.platform_id, 'Runner.platform_id or %s' % (
            '`PLATFORM_ID` env var required (keys in browsers.json)'
        )
        assert self.platform_id in browsers, (
            'platform_id not found in browsers.json'
        )
        return self.platform_id, browsers.get(self.platform_id)

    def will_upload(self):
        return self.prod_run or self.prod_wet_run

    def prep_for_upload(self):
        print 'Fetching upload_secret from GCE Metadata...'
        url = '%s/project/attributes/upload_secret' % self.metadata_url
        res = requests.get(url, headers={'Metadata-Flavor': 'Google'})
        self.upload_secret = res.text
        assert len(self.upload_secret) == 64, (
            'Metadata `upload_secret` must exist for prod runs.')

    def run_is_remote(self):
        return bool(self.platform.get('sauce'))

    def setup_remote_browser(self):
        if self.sauce_user and self.sauce_key and self.sauce_tunnel_id:
            return
        if self.sauce_from_metadata:
            print 'Fetching Sauce creds from GCE metadata...'

            for key in ('sauce_user', 'sauce_key'):
                url = '%s/project/attributes/%s' % (self.metadata_url, key)
                res = requests.get(url, headers={
                    'Metadata-Flavor': 'Google',
                })
                setattr(self, key, res.text)
                assert getattr(self, key, None), (
                    'Metadata key %s is empty.' % key
                )

        assert self.sauce_key, 'Runner.platform.sauce implies %s' % (
            'Runner.sauce_key (Default from `SAUCE_KEY` env var or %s' % (
                'GCE metadata',
            ),
        )
        assert self.sauce_user, 'Runner.platform.sauce implies %s' % (
            'Runner.sauce_user (Default from `SAUCE_USER` env var or %s' % (
                'GCE metadata',
            ),
        )
        self.sauce_tunnel_id = '%s_%s' % (
            self.platform_id, int(time.time()),
        )

    def patch_wpt(self, wptd_path, wpt_path, platform):
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

    def do_run_remote(self):
        # Hack because Sauce expects a different name
        # Maybe just change it in browsers.json?
        if self.platform['browser_name'] == 'edge':
            sauce_browser_name = 'MicrosoftEdge'
        else:
            sauce_browser_name = self.platform['browser_name']
        product = 'sauce:%s:%s' % (
            sauce_browser_name, self.platform['browser_version'],
        )

        command = [
            './wpt', 'run', product,
            '--sauce-platform=%s' % self.platform['os_name'],
            '--sauce-key=%s' % self.sauce_key,
            '--sauce-user=%s' % self.sauce_user,
            '--sauce-tunnel-id=%s' % self.sauce_tunnel_id,
            '--no-restart-on-unexpected',
            '--processes=2',
            '--run-by-dir=3',
            '--log-mach=-',
            '--log-wptreport=%s' % self.local_report_filepath,
            '--install-fonts'
        ]
        if self.run_path:
            command.insert(3, self.run_path)
        return subprocess.call(command, cwd=self.wpt_path)

    def do_run_local(self):
        if self.platform['browser_name'] == "firefox":
            command = [
                'xvfb-run', '--auto-servernum',
                './wpt', 'run',
                self.platform['browser_name'],
                '--install-fonts',
                '--install-browser',
                '--yes',
                '--log-mach=%s' % self.local_log_filepath,
                '--log-wptreport=%s' % self.local_report_filepath,
                # temp fix for webRTC
                '--setpref', 'media.navigator.streams.fake=true',
            ]
            if self.run_path:
                command.insert(5, self.run_path)
        else:
            command = [
                'xvfb-run', '--auto-servernum',
                './wpt', 'run',
                self.platform['browser_name'],
                '--install-fonts',
                '--install-browser',
                '--yes',
                '--log-mach=%s' % self.local_log_filepath,
                '--log-wptreport=%s' % self.local_report_filepath,
            ]
            if self.run_path:
                command.insert(5, self.run_path)

        return subprocess.call(command, cwd=self.wpt_path)

    def load_local_report(self):
        with open(self.local_report_filepath) as f:
            report = json.load(f)

        assert len(report['results']) > 0, (
            '0 test results, something went wrong, stopping.')
        return report

    def report_to_summary(self, report):
        """Parses a WPT report log object into a file-wise summary."""
        test_files = {}

        for result in report['results']:
            test_file = result['test']

            # We expect report to output only one entry per test.
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

    def write_gzip_json(self, filepath, payload):
        try:
            os.makedirs(os.path.dirname(filepath))
        except OSError:
            pass

        with gzip.open(filepath, 'wb') as f:
            payload_str = json.dumps(payload)
            f.write(payload_str)

    def write_result_files(self, report):
        for result in report['results']:
            test_file = result['test']
            filepath = '%s%s' % (self.gs_results_filepath_base, test_file)
            self.write_gzip_json(filepath, result)
            print('Wrote file %s' % filepath)

    def upload_results(self):
        command = ['gsutil', '-m', '-h', 'Content-Encoding:gzip',
                   'rsync', '-r', self.sha, 'gs://wptd/%s' % self.sha]
        return_code = subprocess.check_call(command, cwd=self.output_path)
        assert return_code == 0, 'gsutil rsync return code was not 0!'

    def upload_run(self):
        if self.prod_run:
            final_browser_name = self.platform['browser_name']
        else:
            # The PROD_WET_RUN is identical to PROD_RUN, however the
            # browser name it creates will be prefixed by eval-,
            # causing it to not show up in the dashboard.
            final_browser_name = 'eval-%s' % self.platform['browser_name']
        url = '%s/test-runs' % self.prod_host
        response = requests.post(url, params={
                'secret': self.upload_secret
            },
            data=json.dumps({
                'browser_name': final_browser_name,
                'browser_version': self.platform['browser_version'],
                'os_name': self.platform['os_name'],
                'os_version': self.platform['os_version'],
                'revision': self.sha,
                'results_url': self.gs_http_results_url
            }
        ))
        return response
