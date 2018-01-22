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
    report_to_summary,
    version_string_to_major_minor,
    setup_wpt
)


def stub_patch_wpt(a, b):
    return 0


def stub_check_call(a, cwd):
    return 0


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

    @mock.patch('run.patch_wpt', new=stub_patch_wpt)
    @mock.patch('subprocess.check_call', new=stub_check_call)
    def test_setup_wpt_explicit_sha(self):
        args = Args()
        args.wpt_sha = '1234567890'
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        self.assertEqual(setup_wpt(args, {}, config, logger), args.wpt_sha)

    @mock.patch('shas.SHAFinder')
    @mock.patch('run.patch_wpt', new=stub_patch_wpt)
    @mock.patch('subprocess.check_call', new=stub_check_call)
    def test_setup_wpt_find_sha(self, mock_sha_finder):
        args = Args()
        args.wpt_sha = None
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        wpt_sha = setup_wpt(args, {}, config, logger)
        self.assertNotEqual(wpt_sha, args.wpt_sha)
        self.assertTrue(mock_sha_finder.called)

    @mock.patch('run.patch_wpt')
    @mock.patch('subprocess.check_call', new=stub_check_call)
    def test_setup_wpt_calls_patch_wpt(self, mock_patch_wpt):
        args = Args()
        args.wpt_sha = '1234567890'
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        setup_wpt(args, {}, config, logger)
        self.assertEqual(mock_patch_wpt.called, True)


if __name__ == '__main__':
    unittest.main()
