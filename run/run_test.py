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

import unittest

from run.run import report_to_summary


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


if __name__ == '__main__':
    unittest.main()
