#!/usr/bin/env python

# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import mock
import os
import shas
import unittest

from datetime import date

here = os.path.dirname(__file__)
wptd_dir = os.path.join(here, '../')


class TestSHAFinder(unittest.TestCase):

    def test_nov_21st(self):
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
