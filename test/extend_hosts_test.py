# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
import os
import re
import subprocess
import tempfile
import unittest

here = os.path.dirname(os.path.abspath(__file__))
extend = os.path.sep.join([here, '..', 'src', 'scripts', 'extend-hosts.py'])


def hasLine(filename, content):
    with open(filename) as handle:
        for line in handle:
            if re.match(content + r'\s*(#.*)?$', line.strip()) is not None:
                return True

    return False


class TestExtendHosts(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.mkstemp()[1]

    def tearDown(self):
        os.remove(self.temp_file)

    def extend(self, filename, content):
        proc = subprocess.Popen([extend, filename],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate(content)

        return proc.returncode, stdout, stderr

    def test_non_existent_file(self):
        returncode, stdout, stderr = self.extend('/foo/bar/baz', 'anything')

        self.assertNotEquals(returncode, 0, stdout)

    def test_empty_file(self):
        returncode, stdout, stderr = self.extend(self.temp_file, 'foobar')

        self.assertEquals(returncode, 0, stderr)

        self.assertTrue(hasLine(self.temp_file, 'foobar'))

    def test_no_previous(self):
        with open(self.temp_file, 'w') as handle:
            handle.write('\n'.join(['first', 'second', 'third']))

        returncode, stdout, stderr = self.extend(self.temp_file, 'foobar')

        self.assertEquals(returncode, 0, stderr)

        self.assertTrue(hasLine(self.temp_file, 'first'))
        self.assertTrue(hasLine(self.temp_file, 'second'))
        self.assertTrue(hasLine(self.temp_file, 'third'))
        self.assertTrue(hasLine(self.temp_file, 'foobar'))

    def test_some_previous(self):
        with open(self.temp_file, 'w') as handle:
            handle.write('\n'.join(['first', 'second', 'third']))

        self.extend(self.temp_file, 'foo')

        with open(self.temp_file, 'a') as handle:
            handle.write('\nfourth')

        self.assertTrue(hasLine(self.temp_file, 'first'))
        self.assertTrue(hasLine(self.temp_file, 'second'))
        self.assertTrue(hasLine(self.temp_file, 'third'))
        self.assertTrue(hasLine(self.temp_file, 'foo'))
        self.assertTrue(hasLine(self.temp_file, 'fourth'))

        returncode, stdout, stderr = self.extend(self.temp_file, 'bar')

        self.assertEquals(returncode, 0, stderr)

        self.assertTrue(hasLine(self.temp_file, 'first'))
        self.assertTrue(hasLine(self.temp_file, 'second'))
        self.assertTrue(hasLine(self.temp_file, 'third'))
        self.assertTrue(hasLine(self.temp_file, 'bar'))

        self.assertFalse(hasLine(self.temp_file, 'foo'))

    def test_all_previous(self):
        self.extend(self.temp_file, 'foo')

        self.assertTrue(hasLine(self.temp_file, 'foo'))

        returncode, stdout, stderr = self.extend(self.temp_file, 'bar')

        self.assertEquals(returncode, 0, stderr)

        self.assertTrue(hasLine(self.temp_file, 'bar'))
        self.assertFalse(hasLine(self.temp_file, 'foo'))

    def test_many_lines(self):
        with open(self.temp_file, 'w') as handle:
            handle.write('\n'.join(['first', 'second', 'third']))

        self.extend(self.temp_file, 'foo\nbar\nbaz')

        self.assertTrue(hasLine(self.temp_file, 'first'))
        self.assertTrue(hasLine(self.temp_file, 'second'))
        self.assertTrue(hasLine(self.temp_file, 'third'))
        self.assertTrue(hasLine(self.temp_file, 'foo'))
        self.assertTrue(hasLine(self.temp_file, 'bar'))
        self.assertTrue(hasLine(self.temp_file, 'baz'))

        returncode, stdout, stderr = self.extend(self.temp_file,
                                                 'oof\nrab\nzab')

        self.assertEquals(returncode, 0, stderr)

        self.assertTrue(hasLine(self.temp_file, 'first'))
        self.assertTrue(hasLine(self.temp_file, 'second'))
        self.assertTrue(hasLine(self.temp_file, 'third'))
        self.assertTrue(hasLine(self.temp_file, 'oof'))
        self.assertTrue(hasLine(self.temp_file, 'rab'))
        self.assertTrue(hasLine(self.temp_file, 'zab'))

        self.assertFalse(hasLine(self.temp_file, 'foo'))
        self.assertFalse(hasLine(self.temp_file, 'bar'))
        self.assertFalse(hasLine(self.temp_file, 'baz'))


if __name__ == '__main__':
    unittest.main()
