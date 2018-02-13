# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import gzip
import json
import os
import tempfile


class InsufficientData(Exception):
    pass


class Report(object):
    '''A utility for storing WPT results data spread across multiple segments
    (i.e. "chunks"). Segment data is persisted on disk in order to limit memory
    consumption and support forensics in the case of process failure.'''

    def __init__(self, total_chunks, backing_dir=None):
        if backing_dir is not None:
            self._dir = backing_dir
        else:
            self._dir = tempfile.mkdtemp()

        self._total_chunks = total_chunks

    def _chunk_name(self, chunk_offset):
        if chunk_offset < 1 or chunk_offset > self._total_chunks:
            raise IndexError()

        file_name = '%s-of-%s.json' % (chunk_offset, self._total_chunks)

        return os.path.join(self._dir, file_name)

    def _get_chunk(self, chunk_offset):
        try:
            with open(self._chunk_name(chunk_offset)) as handle:
                contents = handle.read()
        except IOError:
            return {'results': []}

        try:
            return json.loads(contents)
        except ValueError:
            return {'results': []}

    def load_chunk(self, chunk_offset, file_name):
        '''Open a JSON-formatted file representing the results of a given
        "chunk" of tests.

        Raises an `InsufficientData` exception if this dataset does not have
        more results than any previously-loaded dataset for the specified
        "chunk".

        Returns the parsed data.'''

        current = self._get_chunk(chunk_offset)

        with open(file_name) as handle:
            contents = handle.read()

        # The WPT CLI is known to produce invalid JSON files in some
        # circumstances. These cases represent test executions with zero
        # results. Tolerate this condition and interpret accordingly.
        #
        # https://github.com/w3c/web-platform-tests/issues/9481
        try:
            data = json.loads(contents)
        except ValueError:
            data = {'results': []}

        if len(data['results']) <= len(current['results']):
            raise InsufficientData()

        with open(self._chunk_name(chunk_offset), 'w') as handle:
            handle.write(json.dumps(data))

        return data

    def summarize(self):
        '''Create a data structure summarizing the results of all available
        "chunks".

        Raises an `InsufficientData` exception if the dataset contains zero
        test results.'''

        summary = {}
        has_results = False

        for chunk_offset in range(1, self._total_chunks + 1):
            chunk = self._get_chunk(chunk_offset)
            for result in chunk['results']:
                test_file = result['test']
                has_results = True

                assert test_file not in summary, (
                    'test_file "%s" is not already present in summary')

                if result['status'] in ('OK', 'PASS'):
                    summary[test_file] = [1, 1]
                else:
                    summary[test_file] = [0, 1]

                for subtest in result['subtests']:
                    if subtest['status'] == 'PASS':
                        summary[test_file][0] += 1

                    summary[test_file][1] += 1

        if not has_results:
            raise InsufficientData()

        return summary

    def each_result(self):
        '''Iterate over the individual test results described by all available
        "chunks".'''

        for chunk_offset in range(1, self._total_chunks + 1):
            chunk = self._get_chunk(chunk_offset)

            for result in chunk['results']:
                yield result
