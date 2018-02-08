# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import glob
import gzip
import json
import os
import platform
import shutil
import subprocess
import unittest

from testing_tools import command_stubber

here = os.path.dirname(os.path.realpath(__file__))
tools_dir = os.path.join(here, 'testing_tools')
bin_dir = os.path.join(tools_dir, 'bin')
mock_wpt_dir = os.path.join(tools_dir, 'mock-web-platform-tests')
mock_wptd_dir = os.path.join(tools_dir, 'mock-wptdashboard')
log_dir = os.path.join(tools_dir, 'wptdbuild')


class TestRun2(unittest.TestCase):
    def setUp(self):
        self.remote_control = command_stubber.CommandStubber()

        try:
            os.mkdir(log_dir)
            os.mkdir(os.path.join(mock_wptd_dir, 'webapp'))
        except OSError:
            pass

    def tearDown(self):
        shutil.rmtree(log_dir)
        shutil.rmtree(os.path.join(mock_wptd_dir, 'webapp'))

    def write_browsers_manifest(self, data):
        full_path = os.path.join(mock_wptd_dir, 'webapp', 'browsers.json')

        with open(full_path, 'w') as handle:
            handle.write(json.dumps(data))

    def run_py(self, cli_arguments):
        env = dict(os.environ)
        env['PATH'] = bin_dir + ':' + mock_wpt_dir + ':' + env['PATH']
        env['PWD'] = mock_wptd_dir

        command = ['python', os.path.join(here, 'run.py')] + cli_arguments

        return self.remote_control.run(command, cwd=mock_wptd_dir, env=env,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

    def cmd_wpt(self, *args):
        if 'run' in args:
            try:
                index = args.index('--log-wptreport')
            except ValueError:
                return

            full_path = os.path.join(log_dir, args[index + 1])
            with open(full_path, 'w') as log:
                log.write(self.wpt_log_contents)

            # Invocations of `wpt run` are generally expected to fail because
            # most browsers will fail at least one test
            return {'returncode': 1}

    def assertJsonMatch(self, expected, actual):
        def load(path_parts):
            path = os.path.join(*path_parts)

            with gzip.open(path) as handle:
                return json.loads(handle.read())

        self.assertEqual(load(expected), load(actual))

    def test_simple_report_1(self):
        platform_id = 'chrome-64.0-linux'

        def git(*args):
            if 'log' in args:
                return {'stdout': 'deadbeef'}

        self.remote_control.add_handler('git', git)
        self.remote_control.add_handler(
            'chrome', lambda *_: {'stdout': 'Chromium 64.0.3282.119'}
        )
        self.write_browsers_manifest({
            platform_id: {
                'initially_loaded': False,
                'currently_run': False,
                'browser_name': 'chrome',
                'browser_version': '64.0',
                'os_name': platform.system().lower(),
                'os_version': '*'
            }
        })
        self.remote_control.add_handler('wpt', self.cmd_wpt)
        self.wpt_log_file_name = 'wptd-%s-%s-report.log' % (
            'deadbeef', platform_id
        )
        self.wpt_log_contents = json.dumps({
            'results': [
                {
                    'test': '/js/with-statement.html',
                    'status': 'OK',
                    'message': None,
                    'subtests': [
                        {'status': 'PASS', 'message': None, 'name': 'first'},
                        {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                    ]
                },
                {
                    'test': '/js/isNaN.html',
                    'status': 'OK',
                    'message': None,
                    'subtests': [
                        {'status': 'PASS', 'message': None, 'name': 'first'},
                        {'status': 'FAIL', 'message': 'bad', 'name': 'second'},
                        {'status': 'PASS', 'message': None, 'name': 'third'}
                    ]
                }
            ]
        })

        returncode, stdout, stderr = self.run_py([platform_id])

        self.assertEquals(returncode, 0, stderr)

        actual_output_dir = [log_dir, 'deadbeef']
        expected_output_dir = [
            here, 'expected_output', 'simple_report-1', 'deadbeef'
        ]

        self.assertJsonMatch(
            actual_output_dir + ['%s-summary.json.gz' % platform_id],
            expected_output_dir + ['%s-summary.json.gz' % platform_id]
        )
        self.assertJsonMatch(
            actual_output_dir + [platform_id, 'js', 'with-statement.html'],
            expected_output_dir + [platform_id, 'js', 'with-statement.html']
        )
        self.assertJsonMatch(
            actual_output_dir + [platform_id, 'js', 'isNaN.html'],
            expected_output_dir + [platform_id, 'js', 'isNaN.html']
        )

    def test_simple_report_2(self):
        platform_id = 'chrome-62.0-linux'

        def git(*args):
            if 'log' in args:
                return {'stdout': 'c0ffee'}

        self.remote_control.add_handler('git', git)
        self.remote_control.add_handler(
            'chrome', lambda *_: {'stdout': 'Chromium 62.0.3382.22'}
        )
        self.write_browsers_manifest({
            platform_id: {
                'initially_loaded': False,
                'currently_run': False,
                'browser_name': 'chrome',
                'browser_version': '62.0',
                'os_name': platform.system().lower(),
                'os_version': '*'
            }
        })
        self.remote_control.add_handler('wpt', self.cmd_wpt)
        self.wpt_log_file_name = 'wptd-%s-%s-report.log' % (
            'c0ffee', platform_id
        )
        self.wpt_log_contents = json.dumps({
            'results': [
                {
                    'test': '/js/bitwise-or.html',
                    'status': 'OK',
                    'message': None,
                    'subtests': []
                },
                {
                    'test': '/js/bitwise-and.html',
                    'status': 'OK',
                    'message': None,
                    'subtests': [
                        {'status': 'FAIL', 'message': 'bad', 'name': 'first'},
                        {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                    ]
                }
            ]
        })

        returncode, stdout, stderr = self.run_py([platform_id])

        self.assertEqual(returncode, 0, stderr)

        actual_output_dir = [log_dir, 'c0ffee']
        expected_output_dir = [
            here, 'expected_output', 'simple_report-2', 'c0ffee'
        ]

        self.assertJsonMatch(
            actual_output_dir + ['%s-summary.json.gz' % platform_id],
            expected_output_dir + ['%s-summary.json.gz' % platform_id]
        )
        self.assertJsonMatch(
            actual_output_dir + [platform_id, 'js', 'bitwise-or.html'],
            expected_output_dir + [platform_id, 'js', 'bitwise-or.html']
        )
        self.assertJsonMatch(
            actual_output_dir + [platform_id, 'js', 'bitwise-and.html'],
            expected_output_dir + [platform_id, 'js', 'bitwise-and.html']
        )

    def test_repeated_results(self):
        platform_id = 'chrome-62.0-linux'

        def git(*args):
            if 'log' in args:
                return {'stdout': 'c0ffee'}

        self.remote_control.add_handler('git', git)
        self.remote_control.add_handler(
            'chrome', lambda *_: {'stdout': 'Chromium 62.0.3382.22'}
        )
        self.write_browsers_manifest({
            platform_id: {
                'initially_loaded': False,
                'currently_run': False,
                'browser_name': 'chrome',
                'browser_version': '62.0',
                'os_name': platform.system().lower(),
                'os_version': '*'
            }
        })
        self.remote_control.add_handler('wpt', self.cmd_wpt)
        self.wpt_log_file_name = 'wptd-%s-%s-report.log' % (
            'c0ffee', platform_id
        )
        self.wpt_log_contents = json.dumps({
            'results': [
                {
                    'test': '/js/bitwise-or.html',
                    'status': 'OK',
                    'message': None,
                    'subtests': []
                },
                {
                    'test': '/js/bitwise-and.html',
                    'status': 'OK',
                    'message': None,
                    'subtests': [
                        {'status': 'FAIL', 'message': 'bad', 'name': 'first'},
                        {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                    ]
                },
                {
                    'test': '/js/bitwise-or.html',
                    'status': 'OK',
                    'message': None,
                    'subtests': []
                }
            ]
        })

        returncode, stdout, stderr = self.run_py([platform_id])

        self.assertNotEqual(
            returncode,
            0,
            '`run.py` should fail when the `wpt` CLI produces repeated results'
        )
        self.assertListEqual(os.listdir(log_dir), ['c0ffee'])

    def test_os_name_mismatch(self):
        platform_id = 'chrome-63.0-linux'

        def git(*args):
            if 'log' in args:
                return {'stdout': 'c0ffee'}

        self.remote_control.add_handler('git', git)
        self.remote_control.add_handler(
            'chrome', lambda *_: {'stdout': 'Chromium 63.0.3382.22'}
        )
        self.write_browsers_manifest({
            'chrome-63.0-linux': {
                'initially_loaded': False,
                'currently_run': False,
                'browser_name': 'chrome',
                'browser_version': '63.0',
                'os_name': 'WaldronOS',
                'os_version': '*'
            }
        })
        # No handler is defined for the `wpt` CLI so that this test will fail
        # if the `run.py` script invokes it.

        returncode, stdout, stderr = self.run_py([platform_id])

        self.assertNotEqual(returncode, 0, stdout)

    def test_unrecognized_platform_id(self):
        platform_id = 'chrome-63.0-linux'

        def git(*args):
            if 'log' in args:
                return {'stdout': 'c0ffee'}

        self.remote_control.add_handler('git', git)
        self.remote_control.add_handler(
            'chrome', lambda *_: {'stdout': 'Chromium 62.0.3382.22'}
        )
        self.write_browsers_manifest({
            'chrome-12983.0-linux': {
                'initially_loaded': False,
                'currently_run': False,
                'browser_name': 'chrome',
                'browser_version': '12983.0',
                'os_name': platform.system().lower(),
                'os_version': '*'
            }
        })

        # No handler is defined for the `wpt` CLI so that this test will fail
        # if the `run.py` script invokes it.

        returncode, stdout, stderr = self.run_py([platform_id])

        self.assertNotEqual(returncode, 0, stdout)

    def test_git_update_failure(self):
        platform_id = 'chrome-64.0-linux'
        self.update_attempts = 0

        def git(*args):
            if 'pull' in args or 'fetch' in args:
                self.update_attempts += 1
                return {'returncode': 1}
            if 'log' in args:
                return {'stdout': 'c0ffee'}

        self.remote_control.add_handler('git', git)
        self.remote_control.add_handler(
            'chrome', lambda *_: {'stdout': 'Chromium 64.0.3382.22'}
        )
        self.write_browsers_manifest({
            platform_id: {
                'initially_loaded': False,
                'currently_run': False,
                'browser_name': 'chrome',
                'browser_version': '64.0',
                'os_name': platform.system().lower(),
                'os_version': '*'
            }
        })
        # No handler is defined for the `wpt` CLI so that this test will fail
        # if the `run.py` script invokes it.

        returncode, stdout, stderr = self.run_py([platform_id])

        self.assertNotEqual(returncode, 0, stdout)

        self.assertEquals(
            self.update_attempts,
            1,
            '`run.py` attempted to update the WPT git repository'
        )

        self.assertListEqual(os.listdir(log_dir), [])


if __name__ == '__main__':
    unittest.main()
