import unittest

from run import *


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
