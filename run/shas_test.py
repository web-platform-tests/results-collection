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

here = os.path.dirname(__file__)
wptd_dir = os.path.join(here, '../')
target_dir = os.path.abspath(os.path.join(os.path.abspath(wptd_dir), '../', 'wptdashboard-temp'))


if os.path.exists(target_dir):
    print('%s exists, so it will be deleted and recloned for this test' % target_dir)
    shutil.rmtree(target_dir)

os.makedirs(target_dir)
command = ['git', 'clone', '--depth', '1', 'https://github.com/w3c/wptdashboard', target_dir]
return_code = subprocess.check_call(command, cwd=wptd_dir)
assert return_code == 0, ('Got non-0 return code: %d from command %s' % (return_code, command))


class TestSHAFinder(unittest.TestCase):

    def test_nov_21st(self):
        # Travis only pulls git history depth 50 by default
        command = [
            'git',
            'fetch',
            '--unshallow',
        ]
        abspath = os.path.abspath(wptd_dir)
        subprocess.call(command, cwd=target_dir)

        # ~5 commits that day, ensure first is result.
        logger = mock.Mock(logging.Logger)

        sha_finder = shas.SHAFinder(logger, date(2017, 11, 21))

        self.assertEqual('46060eb2c33de6101bc6930bf5e34f794aa9f996',
                         sha_finder.get_todays_sha(wptd_dir))

    def test_nov_18th(self):
        # No commits that day, ensure empty result.
        logger = mock.Mock(logging.Logger)

        sha_finder = shas.SHAFinder(logger, date(2017, 11, 18))

        self.assertEqual('', sha_finder.get_todays_sha(wptd_dir))


if __name__ == '__main__':
    unittest.main()
