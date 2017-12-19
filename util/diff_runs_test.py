#!/usr/bin/env python

# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import logging
import mock
import os
import sys
import unittest

from diff_runs import Fetcher, RunDiffer, PlatformsAtRevision

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(here, '../run/'))
from run_summary import TestRunSpec, TestRunSummary, TestRunSummaryDiff  # noqa


class DiffRunTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_args = mock.Mock(spec=argparse.Namespace)
        self.mock_args.tests = []

        self.mock_fetcher = mock.Mock(spec=Fetcher)
        self.mock_logger = mock.Mock(spec=logging.Logger)

        self.differ = RunDiffer(
            self.mock_args, self.mock_logger, self.mock_fetcher)

    def test_fetch_failure(self):
        self.mock_args.after = PlatformsAtRevision.parse("chrome@latest")
        self.mock_args.before = PlatformsAtRevision.parse("chrome@0123456789")
        self.mock_fetcher.fetchResults.return_value = None

        self.differ.diff()

        # 2 failed-fetch warnings, one 'Diffing . and ." info
        self.assertEqual(self.mock_logger.warning.call_count, 2)
        self.mock_logger.info.assert_called_once()

    def test_no_difference(self):
        self.mock_args.after = PlatformsAtRevision.parse("chrome@latest")
        self.mock_args.before = PlatformsAtRevision.parse("chrome@0123456789")

        def result(spec):
            return TestRunSummary(spec, {
                '/mock/path.html': [1, 1],
                '/mock/path_2.html': [3, 5],
            })
        self.mock_fetcher.fetchResults.side_effect = result

        self.differ.diff()

        logged = self.mock_logger.info.call_args[0][0]
        self.assertIn('0 differences', logged)
        self.assertIn('2 tests', logged)

    def test_removes_all(self):
        self.mock_args.after = PlatformsAtRevision.parse("chrome@latest")
        self.mock_args.before = PlatformsAtRevision.parse("chrome@0123456789")

        def results(spec):
            if spec.sha == 'latest':
                return TestRunSummary(spec, {})
            if spec.sha == '0123456789':
                return TestRunSummary(spec, {
                    '/mock/path.html': [1, 1],
                    '/mock/path2.html': [1, 2]
                })
        self.mock_fetcher.fetchResults.side_effect = results

        self.differ.diff()

        logged = self.mock_logger.info.call_args[0][0]
        self.assertIn('2 tests ran in', logged)
        self.assertIn('but not in', logged)

    def test_one_difference(self):
        self.mock_args.after = PlatformsAtRevision.parse("chrome@latest")
        self.mock_args.before = PlatformsAtRevision.parse("chrome@0123456789")

        def results(spec):  # type: (TestRunSpec) -> TestRunSummary
            if spec.sha == 'latest':
                return TestRunSummary(spec, {
                    '/mock/path.html': [0, 1]
                })
            if spec.sha == '0123456789':
                return TestRunSummary(spec, {
                    '/mock/path.html': [1, 1]
                })
        self.mock_fetcher.fetchResults.side_effect = results

        self.differ.diff()

        logged = self.mock_logger.info.call_args[0][0]
        self.assertIn('1 differences', logged)
        self.assertIn('1 tests', logged)

    def test_cull_ignored_tests_dir(self):
        results = {
            '/css/foo.html': [1, 1],
            '/css/bar.html': [1, 1],
            '/html/baz.html': [0, 1]
        }
        tests = ['/css/']
        self.differ.cull_ignored_tests(results, tests)
        self.assertIn('/css/foo.html', results)
        self.assertIn('/css/bar.html', results)
        self.assertNotIn('/html/baz.html', results)

    def test_cull_ignored_tests_specific_test(self):
        results = {
            '/css/foo.html': [1, 1],
            '/css/bar.html': [1, 1],
        }
        tests = ['/css/foo.html']
        self.differ.cull_ignored_tests(results, tests)
        self.assertIn('/css/foo.html', results)
        self.assertNotIn('/css/bar.html', results)


if __name__ == '__main__':
    unittest.main()
