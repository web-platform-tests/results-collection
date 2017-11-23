#!/usr/bin/env python
#
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
        logger = mock.Mock(logging.Logger)

        sha_finder = shas.SHAFinder(logger, date(2017, 11, 21))

        self.assertEqual('46060eb2c33de6101bc6930bf5e34f794aa9f996',
                         sha_finder.get_todays_sha(wptd_dir))


if __name__ == '__main__':
    unittest.main()
