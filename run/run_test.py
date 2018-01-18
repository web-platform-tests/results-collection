# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import mock
import os
import shas
import subprocess
import unittest

from run import (
    report_to_summary,
    version_string_to_major_minor,
    setup_wpt
)

import run


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

    def test_setup_wpt_explicit_sha(self):
        run.patch_wpt = stub_patch_wpt
        subprocess.check_call = stub_check_call

        args = Args()
        args.wpt_sha = '1234567890'
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        self.assertEqual(setup_wpt(args, {}, config, logger), args.wpt_sha)

    def test_setup_wpt_find_sha(self):
        run.patch_wpt = stub_patch_wpt
        subprocess.check_call = stub_check_call

        originalSHAFinder = shas.SHAFinder
        shas.SHAFinder = mock.Mock(shas.SHAFinder)

        args = Args()
        args.wpt_sha = None
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        self.assertNotEqual(setup_wpt(args, {}, config, logger), args.wpt_sha)
        self.assertEqual(shas.SHAFinder.called, True)

        shas.SHAFinder = originalSHAFinder

    def test_setup_wpt_calls_patch_wpt(self):
        run.patch_wpt = mock.Mock(run.patch_wpt)
        subprocess.check_call = stub_check_call

        args = Args()
        args.wpt_sha = '1234567890'
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        setup_wpt(args, {}, config, logger)
        self.assertEqual(run.patch_wpt.called, True)


if __name__ == '__main__':
    unittest.main()
