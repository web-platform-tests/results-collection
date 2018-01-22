# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import mock
import os
import run
import shas
import subprocess
import unittest

from run import (
    get_commit_details,
    patch_wpt,
    report_to_summary,
    setup_wpt,
    version_string_to_major_minor
)


def stub_patch_wpt(a, b):
    return 0


def stub_call(a, cwd):
    # This represents a return code
    return 0


def stub_check_call(a, cwd):
    # This represents a return code
    return 0


def stub_check_output(a, cwd):
    # The actual stdout is expected from check_output,
    # not a return code
    return '1'


class Args:
    def __init__(self):
        self.wpt_sha = ''


logger = mock.Mock(logging.Logger)


class TestRun(unittest.TestCase):

    def test_report_to_summary(self):
        actual = report_to_summary({
            'results': [
                {
                    'test': '/dom/a.html',
                    'status': 'OK',
                    'subtests': [
                        {'status': 'PASS'}
                    ]
                },
                {
                    'test': '/dom/b.html',
                    'status': 'OK',
                    'subtests': [
                        {'status': 'FAIL'}
                    ]
                }
            ]
        })
        self.assertEqual(actual, {
            '/dom/a.html': [2, 2],
            '/dom/b.html': [1, 2],
        })

    def test_version_string_to_major_minor(self):
        with self.assertRaises(AssertionError):
            version_string_to_major_minor('')
        self.assertEqual(version_string_to_major_minor('1.1'), '1.1')
        self.assertEqual(version_string_to_major_minor('1.1.1'), '1.1')

    @mock.patch('subprocess.check_call', side_effect=stub_check_call)
    def test_setup_wpt(self, mock_check_call):
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        return_value = setup_wpt(config)

        self.assertEqual(return_value, 0)
        # TODO: assert details about mock_call.call_args
        self.assertTrue(mock_check_call.called)
        # TODO: assert details about mock_check_output.call_args
        self.assertEqual(mock_check_call.call_count, 4)

    @mock.patch('subprocess.call', side_effect=stub_call)
    @mock.patch('subprocess.check_output', side_effect=stub_check_output)
    def test_get_commit_details_explicit_sha(self,
                                             mock_call,
                                             mock_check_output):
        args = Args()
        args.wpt_sha = '1234567890'
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        wpt_sha, wpt_date = get_commit_details(args, config, logger)

        self.assertEqual(wpt_sha, args.wpt_sha)
        self.assertEqual(wpt_date, '1')
        # TODO: assert details about mock_check_output.call_args
        self.assertTrue(mock_call.called)
        self.assertTrue(mock_check_output.called)

    @mock.patch('shas.SHAFinder')
    @mock.patch('subprocess.call', side_effect=stub_call)
    @mock.patch('subprocess.check_output', side_effect=stub_check_output)
    def test_get_commit_details_find_sha(self,
                                         mock_sha_finder,
                                         mock_call,
                                         mock_check_output):
        args = Args()
        args.wpt_sha = None
        config = {
            'wpt_path': os.path.dirname(os.path.realpath(__file__))
        }

        wpt_sha, wpt_date = get_commit_details(args, config, logger)

        self.assertNotEqual(wpt_sha, args.wpt_sha)
        self.assertTrue(mock_sha_finder.called)
        self.assertTrue(mock_call.called)


if __name__ == '__main__':
    unittest.main()
