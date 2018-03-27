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
validate = os.path.sep.join([
    here, '..', 'src', 'scripts', 'validate-wpt-results.py'
])


def make_results(count):
    results = {'results': []}
    test_filenames = []

    for idx in range(count):
        test_filename = '/%s.html' % idx
        subtests = []
        for jdx in range(count % 5):
            subtests.append({
                'status': 'PASS' if jdx % 2 else 'FAIL',
                'message': 'message for %s' % jdx,
                'name': 'subtest %s' % jdx
            })

        test_filenames.append(test_filename)
        results['results'].append({
            'test': test_filename,
            'status': 'OK',
            'subtests': subtests
        })

    return results, test_filenames


class ValidateWptResults(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def temp_file(self, name):
        return os.path.join(self.temp_dir, name)

    def validate(self, log_wptreport, log_raw):
        proc = subprocess.Popen([
            validate, '--log-wptreport', log_wptreport, '--log-raw', log_raw
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()

        return (proc.returncode, stdout, stderr)

    def test_perfect(self):
        results, filenames = make_results(6)
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')

        with open(log_wptreport, 'w') as handle:
            json.dump(results, handle)

        with open(log_raw, 'w') as handle:
            handle.write(
                json.dumps({
                    'action': 'suite_start',
                    'tests': {
                        'default': filenames
                    }
                })
            )

        returncode, stdout, stderr = self.validate(log_wptreport, log_raw)

        self.assertEquals(returncode, 0, stderr)

    def test_zero_tests(self):
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')

        with open(log_wptreport, 'w') as handle:
            json.dump({'results': []}, handle)

        with open(log_raw, 'w') as handle:
            handle.write(
                json.dumps({
                    'action': 'suite_start',
                    'tests': {
                        'default': []
                    }
                })
            )

        returncode, stdout, stderr = self.validate(log_wptreport, log_raw)

        self.assertEquals(returncode, 0, stderr)

    def test_extra_log_raw(self):
        results, filenames = make_results(6)
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')

        with open(log_wptreport, 'w') as handle:
            json.dump(results, handle)

        with open(log_raw, 'w') as handle:
            handle.write('''
            {}
            {"action": "other"}
            {"action": "other", "tests": []}
            %s
            {}
            {"action": "other"}
            {"action": "other", "tests": []}''' % (
                json.dumps({
                    'action': 'suite_start',
                    'tests': {
                        'default': filenames
                    }
                }))
            )

        returncode, stdout, stderr = self.validate(log_wptreport, log_raw)

        self.assertEquals(returncode, 0, stderr)

    def test_empty_log_raw(self):
        results, filenames = make_results(6)
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')

        with open(log_wptreport, 'w') as handle:
            json.dump(results, handle)

        with open(log_raw, 'w') as handle:
            handle.write('')

        returncode, stdout, stderr = self.validate(log_wptreport, log_raw)

        self.assertEquals(returncode, 1, stderr)

    def test_missing_acceptable(self):
        results, filenames = make_results(100)
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')

        del results['results'][23]

        with open(log_wptreport, 'w') as handle:
            json.dump(results, handle)

        with open(log_raw, 'w') as handle:
            handle.write(
                json.dumps({
                    'action': 'suite_start',
                    'tests': {
                        'default': filenames
                    }
                })
            )

        returncode, stdout, stderr = self.validate(log_wptreport, log_raw)

        self.assertEquals(returncode, 0, stderr)

    def test_missing_unacceptable(self):
        results, filenames = make_results(100)
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')

        del results['results'][23]
        del results['results'][45]

        with open(log_wptreport, 'w') as handle:
            json.dump(results, handle)

        with open(log_raw, 'w') as handle:
            handle.write(
                json.dumps({
                    'action': 'suite_start',
                    'tests': {
                        'default': filenames
                    }
                })
            )

        returncode, stdout, stderr = self.validate(log_wptreport, log_raw)

        self.assertEquals(returncode, 1, stdout)

    def test_extra_acceptable(self):
        results, filenames = make_results(100)
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')

        del filenames[33]

        with open(log_wptreport, 'w') as handle:
            json.dump(results, handle)

        with open(log_raw, 'w') as handle:
            handle.write(
                json.dumps({
                    'action': 'suite_start',
                    'tests': {
                        'default': filenames
                    }
                })
            )

        returncode, stdout, stderr = self.validate(log_wptreport, log_raw)

        self.assertEquals(returncode, 0, stderr)

    def test_missing_unacceptable(self):
        results, filenames = make_results(100)
        log_wptreport = self.temp_file('wpt-log.json')
        log_raw = self.temp_file('raw-log.json')

        del filenames[33]
        del filenames[66]

        with open(log_wptreport, 'w') as handle:
            json.dump(results, handle)

        with open(log_raw, 'w') as handle:
            handle.write(
                json.dumps({
                    'action': 'suite_start',
                    'tests': {
                        'default': filenames
                    }
                })
            )

        returncode, stdout, stderr = self.validate(log_wptreport, log_raw)

        self.assertEquals(returncode, 1, stdout)
