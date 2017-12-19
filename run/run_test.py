# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from run import (
    report_to_summary,
    version_string_to_major_minor
)


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


if __name__ == '__main__':
    unittest.main()
