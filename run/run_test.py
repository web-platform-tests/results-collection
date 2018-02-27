# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import mock
import os
import run
import shas
import StringIO
import subprocess
import unittest

from run import (
    get_commit_details,
    setup_wpt,
    version_string_to_major_minor
)


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


class FakePopen(object):
    returncode = 0

    def __init__(self, *_, **__):
        self.stdout = StringIO.StringIO()
        self.stdout.__enter__ = lambda *x: None
        self.stdout.__exit__ = lambda *x: None
        self.stderr = StringIO.StringIO()
        self.stderr.__enter__ = lambda *x: None
        self.stderr.__exit__ = lambda *x: None

    def wait(self):
        pass


def stub_popen(*_, **__):
    return FakePopen()


class Args:
    def __init__(self):
        self.wpt_sha = ''


logger = mock.Mock(logging.Logger)


class TestRun(unittest.TestCase):

    def test_version_string_to_major_minor(self):
        with self.assertRaises(AssertionError):
            version_string_to_major_minor('')
        self.assertEqual(version_string_to_major_minor('1.1'), '1.1')
        self.assertEqual(version_string_to_major_minor('1.1.1'), '1.1')

    @mock.patch('subprocess.check_call', side_effect=stub_check_call)
    @mock.patch('subprocess.Popen', side_effect=stub_popen)
    def test_setup_wpt(self, mock_check_call, mock_subproc_popen):
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        return_value = setup_wpt(config, logger)

        self.assertEqual(return_value, 0)
        # TODO: assert details about mock_call.call_args
        self.assertTrue(mock_check_call.called)
        # TODO: assert details about mock_check_output.call_args
        self.assertEqual(mock_check_call.call_count, 3)

    @mock.patch('subprocess.check_output', side_effect=stub_check_output)
    def test_get_commit_details_explicit_sha(self, mock_check_output):
        args = Args()
        args.wpt_sha = '1234567890'
        config = {'wpt_path': os.path.dirname(os.path.realpath(__file__))}

        wpt_sha, wpt_date = get_commit_details(args, config, logger)

        self.assertEqual(wpt_sha, args.wpt_sha)
        self.assertEqual(wpt_date, '1')

    @mock.patch('shas.SHAFinder')
    @mock.patch('subprocess.Popen', side_effect=stub_popen)
    @mock.patch('subprocess.check_output', side_effect=stub_check_output)
    def test_get_commit_details_find_sha(self,
                                         mock_sha_finder,
                                         mock_subproc_popen,
                                         mock_check_output):
        args = Args()
        args.wpt_sha = None
        config = {
            'wpt_path': os.path.dirname(os.path.realpath(__file__))
        }

        wpt_sha, wpt_date = get_commit_details(args, config, logger)

        self.assertNotEqual(wpt_sha, args.wpt_sha)
        self.assertTrue(mock_sha_finder.called)


if __name__ == '__main__':
    unittest.main()
