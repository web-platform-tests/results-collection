#!/usr/bin/env python

# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import mock
import os
import shas
import shutil
import subprocess
import unittest

from datetime import date


class TestSHAFinder(unittest.TestCase):
    here = os.path.dirname(__file__)
    wptd_dir = os.path.join(here, '../')
    target_dir = os.path.abspath(
        os.path.join(os.path.abspath(wptd_dir), '../', 'wptdashboard-temp')
    )
    def setUp(self):
        # This is only necessary for local development environments
        # that are unlikely to have been cloned with an explicit --depth
        if os.path.exists(self.target_dir):
            shutil.rmtree(self.target_dir)

        command = [
            'git', 'clone', '--depth', '1', 'https://github.com/w3c/wptdashboard',
            self.target_dir
        ]
        return_code = subprocess.check_call(command, cwd=self.wptd_dir)
        assert return_code == 0, (
            'Got non-0 return code: %d from command %s' % (return_code, command)
        )


    def test_nov_21st(self):
        # Travis only pulls git history depth 50 by default
        command = [
            'git',
            'fetch',
            '--unshallow',
        ]
        abspath = os.path.abspath(self.wptd_dir)
        subprocess.call(command, cwd=self.target_dir)

        # ~5 commits that day, ensure first is result.
        logger = mock.Mock(logging.Logger)

        sha_finder = shas.SHAFinder(logger, date(2017, 11, 21))

        self.assertEqual(
            '46060eb2c33de6101bc6930bf5e34f794aa9f996',
            sha_finder.get_todays_sha(self.wptd_dir)
        )

    def test_nov_18th(self):
        # No commits that day, ensure empty result.
        logger = mock.Mock(logging.Logger)

        sha_finder = shas.SHAFinder(logger, date(2017, 11, 18))

        self.assertEqual('', sha_finder.get_todays_sha(self.wptd_dir))


if __name__ == '__main__':
    unittest.main()
