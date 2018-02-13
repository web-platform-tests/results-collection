# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import os
import shutil
import tempfile
import unittest

import report


class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def write_json(self, name, data):
        with open(name, 'w') as handle:
            handle.write(json.dumps(data))

    def test_chunk_load(self):
        r = report.Report(3, self.tmp_dir)
        name = os.path.join(self.tmp_dir, 'foo.json')

        self.write_json(name, {'results': [1, 2, 3]})

        result = r.load_chunk(1, name)

        self.assertEquals({'results': [1, 2, 3]}, result)

    def test_chunk_load_no_results(self):
        r = report.Report(3, self.tmp_dir)
        name = os.path.join(self.tmp_dir, 'foo.json')

        self.write_json(name, {'results': []})

        with self.assertRaises(report.InsufficientData):
            r.load_chunk(1, name)

    def test_chunk_load_fewer_results(self):
        r = report.Report(3, self.tmp_dir)
        name = os.path.join(self.tmp_dir, 'foo.json')

        self.write_json(name, {'results': [1, 2, 3]})

        r.load_chunk(1, name)

        self.write_json(name, {'results': [1, 2]})

        with self.assertRaises(report.InsufficientData):
            r.load_chunk(1, name)

    def test_chunk_load_more_results(self):
        r = report.Report(3, self.tmp_dir)
        name = os.path.join(self.tmp_dir, 'foo.json')

        self.write_json(name, {'results': [1, 2, 3]})

        r.load_chunk(1, name)

        self.write_json(name, {'results': [1, 2, 3, 4]})

        result = r.load_chunk(1, name)

        self.assertEquals(result, {'results': [1, 2, 3, 4]})

    def test_chunk_load_oob(self):
        r = report.Report(3, self.tmp_dir)
        name = os.path.join(self.tmp_dir, 'foo.json')

        self.write_json(name, {'results': [1, 2, 3]})

        with self.assertRaises(IndexError):
            r.load_chunk(0, name)

        with self.assertRaises(IndexError):
            r.load_chunk(4, name)

    def test_summarize_one_chunk(self):
        r = report.Report(1, self.tmp_dir)

        name = os.path.join(self.tmp_dir, 'bar.json')

        self.write_json(name, {'results': [
            {
                'test': '/js/with-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                ]
            },
            {
                'test': '/js/isNaN.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'},
                    {'status': 'PASS', 'message': None, 'name': 'third'}
                ]
            }
        ]})

        r.load_chunk(1, name)

        self.assertEqual(r.summarize(), {
            '/js/with-statement.html': [2, 3],
            '/js/isNaN.html': [3, 4]
        })

    def test_summarize_many_chunks_complete(self):
        r = report.Report(3, self.tmp_dir)

        names = [
            os.path.join(self.tmp_dir, 'foo.json'),
            os.path.join(self.tmp_dir, 'bar.json'),
            os.path.join(self.tmp_dir, 'baz.json')
        ]

        self.write_json(names[0], {'results': [
            {
                'test': '/js/with-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                ]
            },
            {
                'test': '/js/isNaN.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'},
                    {'status': 'PASS', 'message': None, 'name': 'third'}
                ]
            }
        ]})
        self.write_json(names[1], {'results': [
            {
                'test': '/js/do-while-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'}
                ]
            },
            {
                'test': '/js/symbol-unscopables.html',
                'status': 'TIMEOUT',
                'message': None,
                'subtests': []
            }
        ]})
        self.write_json(names[2], {'results': [
            {
                'test': '/js/void-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'third'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'fourth'}
                ]
            }
        ]})

        r.load_chunk(1, names[0])
        r.load_chunk(2, names[1])
        r.load_chunk(3, names[2])

        self.assertEqual(r.summarize(), {
            '/js/with-statement.html': [2, 3],
            '/js/isNaN.html': [3, 4],
            '/js/do-while-statement.html': [2, 2],
            '/js/symbol-unscopables.html': [0, 1],
            '/js/void-statement.html': [2, 5]
        })

    def test_summarize_many_chunks_partial(self):
        r = report.Report(3, self.tmp_dir)

        names = [
            os.path.join(self.tmp_dir, 'foo.json'),
            os.path.join(self.tmp_dir, 'baz.json')
        ]

        self.write_json(names[0], {'results': [
            {
                'test': '/js/with-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                ]
            }
        ]})
        self.write_json(names[1], {'results': [
            {
                'test': '/js/void-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'third'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'fourth'}
                ]
            }
        ]})

        r.load_chunk(1, names[0])
        r.load_chunk(3, names[1])

        self.assertEqual(r.summarize(), {
            '/js/with-statement.html': [2, 3],
            '/js/void-statement.html': [2, 5]
        })

    def test_summarize_zero_results(self):
        r = report.Report(3, self.tmp_dir)

        with self.assertRaises(report.InsufficientData):
            r.summarize()

    def test_summarize_repeated_result(self):
        r = report.Report(2, self.tmp_dir)

        names = [
            os.path.join(self.tmp_dir, 'foo.json'),
            os.path.join(self.tmp_dir, 'baz.json')
        ]

        self.write_json(names[0], {'results': [
            {
                'test': '/js/with-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                ]
            }
        ]})
        self.write_json(names[1], {'results': [
            {
                'test': '/js/with-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'third'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'fourth'}
                ]
            }
        ]})

        r.load_chunk(1, names[0])
        r.load_chunk(2, names[1])

        with self.assertRaises(Exception):
            r.summarize()

    def test_each_result(self):
        r = report.Report(3, self.tmp_dir)

        names = [
            os.path.join(self.tmp_dir, 'foo.json'),
            os.path.join(self.tmp_dir, 'bar.json'),
            os.path.join(self.tmp_dir, 'baz.json')
        ]

        expected_results = [
            {
                'test': '/js/with-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                ]
            },
            {
                'test': '/js/isNaN.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'},
                    {'status': 'PASS', 'message': None, 'name': 'third'}
                ]
            },
            {
                'test': '/js/do-while-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'}
                ]
            },
            {
                'test': '/js/symbol-unscopables.html',
                'status': 'TIMEOUT',
                'message': None,
                'subtests': []
            },
            {
                'test': '/js/void-statement.html',
                'status': 'OK',
                'message': None,
                'subtests': [
                    {'status': 'PASS', 'message': None, 'name': 'first'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'second'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'third'},
                    {'status': 'FAIL', 'message': 'bad', 'name': 'fourth'}
                ]
            }
        ]
        self.write_json(names[0], {'results': expected_results[0:2]})
        self.write_json(names[1], {'results': expected_results[2:3]})
        self.write_json(names[2], {'results': expected_results[3:]})

        r.load_chunk(1, names[0])
        r.load_chunk(2, names[1])
        r.load_chunk(3, names[2])

        os.remove(names[0])
        os.remove(names[1])
        os.remove(names[2])

        self.assertItemsEqual(
            [result for result in r.each_result()], expected_results
        )


if __name__ == '__main__':
    unittest.main()
