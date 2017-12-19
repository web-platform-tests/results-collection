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

import json
import os
import re
import unittest


VALID_PLATFORM_ID_REGEX = r"^[a-z0-9\-\.]+$"
REQUIRED_PLATFORM_FIELDS = {
    'currently_run': (True, False),
    'initially_loaded': (True, False),
    'browser_name': ('chrome', 'firefox', 'edge', 'safari'),
    'browser_version': None,
    'os_name': ('linux', 'windows', 'macos'),
    'os_version': None,
}


class TestBrowsers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        filepath = os.path.join(os.path.dirname(__file__),
                                os.pardir, 'webapp', 'browsers.json')
        with open(filepath) as f:
            cls.browsers = json.load(f)

    def test_all_platforms_have_only_valid_characters(self):
        for platform_id, platform_info in self.browsers.items():
            self.assertTrue(
                re.match(VALID_PLATFORM_ID_REGEX, platform_id),
                'platform_id with invalid characters: %s' % platform_id
            )

    def test_all_browsers_have_required_fields(self):
        for platform_id, platform_info in self.browsers.items():
            for key, valid_values in REQUIRED_PLATFORM_FIELDS.items():
                self.assertTrue(
                    key in platform_info.keys(),
                    'Required field missing: %s (platform %s)' %
                    (key, platform_id))

                if REQUIRED_PLATFORM_FIELDS[key] is not None:
                    self.assertTrue(
                        platform_info[key] in REQUIRED_PLATFORM_FIELDS[key],
                        'Field has invalid value: %s (platform %s)'
                        % (key, platform_id))

    def test_no_two_browser_configs_are_equal(self):
        for first_platform_id, first_platform in self.browsers.items():
            identical_platforms = [
                second_platform for second_platform_id, second_platform
                in self.browsers.items()
                if second_platform == first_platform
            ]
            self.assertEqual(
                len(identical_platforms),
                1,
                'Duplicate platforms detected: %s' % identical_platforms)


if __name__ == '__main__':
    unittest.main()
