# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import os
import shutil
import subprocess
import tempfile
import unittest

here = os.path.dirname(os.path.abspath(__file__))
wpt_stub_directory = os.path.sep.join([here, 'bin-stubs'])
validate = os.path.sep.join([
    here, '..', 'src', 'scripts', 'run-and-verify.py'
])
fixture_dir = os.path.sep.join([here, 'wpt-output-fixtures'])


class RunAndVerify(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def temp_file(self, name):
        return os.path.join(self.temp_dir, name)

    def run_and_verify(self, fixture_name, max_attempts):
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')
        count_file = os.path.join(self.temp_dir, 'count.txt')
        fixture_file = os.path.join(fixture_dir, '%s.json' % fixture_name)
        command = [
            validate, '--max-attempts', str(max_attempts), '--log-wptreport',
            log_wptreport, '--log-raw', log_raw
        ]
        with open(count_file, 'w') as handle:
            handle.write('0')

        env = dict(os.environ)
        env['TEST_FIXTURE_FILE'] = fixture_file
        env['TEST_COUNT_FILE'] = count_file

        proc = subprocess.Popen(
            command, cwd=wpt_stub_directory, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout, stderr = proc.communicate()

        with open(count_file) as handle:
            return {
                'attempt_count': int(handle.read()),
                'returncode': proc.returncode,
                'log_wptreport': log_wptreport,
                'stdout': stdout,
                'stderr': stderr
            }

    def assert_success(self, result):
        self.assertEquals(result['returncode'], 0, result['stderr'])

        with open(result['log_wptreport']) as handle:
            json.load(handle)

    def assert_failure(self, result):
        self.assertNotEquals(result['returncode'], 0, result['stdout'])

        self.assertFalse(os.path.isfile(result['log_wptreport']))

    def test_perfect(self):
        result = self.run_and_verify('complete', 1)

        self.assert_success(result)
        self.assertEquals(result['attempt_count'], 1)

    def test_perfect_unused_retry(self):
        result = self.run_and_verify('complete', 3)

        self.assert_success(result)
        self.assertEquals(result['attempt_count'], 1)

    def test_missing_fail(self):
        result = self.run_and_verify('missing-complete', 1)

        self.assert_failure(result)
        self.assertEquals(result['attempt_count'], 1)

    def test_missing_recover(self):
        result = self.run_and_verify('missing-complete', 2)

        self.assert_success(result)
        self.assertEquals(result['attempt_count'], 2)

    def test_extra_fail(self):
        result = self.run_and_verify('extra-complete', 1)

        self.assert_failure(result)
        self.assertEquals(result['attempt_count'], 1)

    def test_extra_recover(self):
        result = self.run_and_verify('extra-complete', 2)

        self.assert_success(result)
        self.assertEquals(result['attempt_count'], 2)

    def test_missingandextra_fail(self):
        result = self.run_and_verify('missingandextra-complete', 1)

        self.assert_failure(result)
        self.assertEquals(result['attempt_count'], 1)

    def test_missingandextra_recover(self):
        result = self.run_and_verify('missingandextra-complete', 2)

        self.assert_success(result)
        self.assertEquals(result['attempt_count'], 2)

    def test_extra_missing_fail(self):
        result = self.run_and_verify('extra-missing-complete', 2)

        self.assert_failure(result)
        self.assertEquals(result['attempt_count'], 2)

    def test_extra_missing_recover(self):
        result = self.run_and_verify('extra-missing-complete', 3)

        self.assert_success(result)
        self.assertEquals(result['attempt_count'], 3)

    def test_no_expectation_fail(self):
        result = self.run_and_verify('noexpect-complete', 1)

        self.assert_failure(result)
        self.assertEquals(result['attempt_count'], 1)

    def test_no_expectation_recover(self):
        result = self.run_and_verify('noexpect-complete', 2)

        self.assert_success(result)
        self.assertEquals(result['attempt_count'], 2)

    def test_allow_missing_jsshell(self):
        result = self.run_and_verify('missing-jsshell', 1)

        self.assert_success(result)
        self.assertEquals(result['attempt_count'], 1)
