#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
import argparse
import contextlib
import distutils.util
import gzip
import json
import logging
import os
import requests
import tempfile


def main(raw_results_directory, product, browser_channel, browser_version,
         os_name, os_version, url, user_name, secret, override_platform,
         total_chunks, git_branch, no_timestamps):
    '''Consolidate the WPT results data into a single JSON file and upload to
    the WPT results receiver.

    The input WPT results data is expected to meet the requirements of the
    results receiver:
    https://github.com/web-platform-tests/wpt.fyi/blob/master/api/README.md#results-creation
    '''

    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level='INFO', format=log_format)
    logger = logging.getLogger('upload-results')
    raw_results_files = [
        os.path.join(raw_results_directory, filename)
        for filename in os.listdir(raw_results_directory)
    ]

    # This script will be scheduled for execution only when all results are
    # available. Under normal operating conditions, this ensures that only
    # complete results sets are uploaded. However, due to the delay between
    # scheduling and uploading, extenuating circumstances can alter the set of
    # available results. Verify the availability of results files to avoid
    # uploading incomplete results sets.
    logger.info('Expected %s results files; found %s' % (
        len(raw_results_files), total_chunks
    ))
    if len(raw_results_files) != total_chunks:
        raise Exception('Found unexpected number of results files.')

    with tmpfile() as filename:
        with gzip.open(filename, 'w') as handle:
            metadata = None

            handle.write('{"results":\n')

            for data in consolidate(raw_results_files, no_timestamps):
                if isinstance(data, str):
                    handle.write(data)
                else:
                    metadata = data

            # When the report is missing critical metadata, extend it with
            # information provided via the command-line. (Currently, the WPT
            # CLI does not include this metadata in reports generated via the
            # Sauce Labs service.)
            if override_platform:
                metadata['run_info'].update({
                            'product': product,
                            'browser_version': browser_version,
                            'os': os_name,
                            'os_version': os_version
                        })

            serialized_metadata = '"run_info":{}'.format(
                json.dumps(metadata['run_info'])
            )
            if (metadata['time_start'] != float('inf')
                    and metadata['time_end'] != 0):
                serialized_metadata += (
                    ', "time_start":{}, "time_end":{}'.format(
                        metadata['time_start'], metadata['time_end']
                    )
                )

            handle.write(',\n%s}\n' % serialized_metadata)

        response = requests.post(
            url,
            auth=(user_name, secret),
            # `labels` is a comma-separated string. Runners may add arbitrary
            # labels.
            data={'labels': ','.join([git_branch, browser_channel])},
            files={'result_file': open(filename, 'rb')}
        )

    logger.info('Response status code: %s', response.status_code)
    logger.info('Response text: %s', response.text)

    assert response.status_code >= 200 and response.status_code < 300, (
           response.text)


@contextlib.contextmanager
def tmpfile():
    fd, temp_filename = tempfile.mkstemp('.json')
    yield temp_filename

    os.close(fd)
    os.remove(temp_filename)


def consolidate(raw_results_files, no_timestamps):
    metadata = {
        'time_start': float('inf'),
        'time_end': 0,
        'run_info': None
    }
    emitted_result = False

    yield '['

    for filename in raw_results_files:
        with open(filename) as handle:
            data = json.load(handle)

        assert 'run_info' in data
        metadata['run_info'] = data['run_info']

        if no_timestamps:
            assert 'time_start' not in data
            assert 'time_end' not in data
        else:
            assert 'time_start' in data
            assert 'time_end' in data
            metadata['time_start'] = min(data.get('time_start', float('inf')),
                                         metadata['time_start'])
            metadata['time_end'] = max(data.get('time_end', 0),
                                       metadata['time_end'])

        assert 'results' in data
        assert isinstance(data['results'], list)

        for result in data['results']:
            text = json.dumps(result)
            if emitted_result:
                text = ',' + text
            else:
                emitted_result = True

            yield text

    yield ']'

    assert isinstance(metadata['run_info'], object)
    yield metadata


parser = argparse.ArgumentParser(description=main.__doc__)
parser.add_argument('--raw-results-directory', required=True)
parser.add_argument('--product', required=True)
parser.add_argument('--browser-channel',
                    choices=('stable', 'experimental'),
                    required=True)
parser.add_argument('--browser-version', required=True)
parser.add_argument('--os', dest='os_name', required=True)
parser.add_argument('--os-version', required=True)
parser.add_argument('--url', required=True)
parser.add_argument('--user-name', required=True)
parser.add_argument('--secret', required=True)
parser.add_argument('--override-platform',
                    type=lambda x: bool(distutils.util.strtobool(x)),
                    required=True)
parser.add_argument('--total-chunks', type=int, required=True)
parser.add_argument('--git-branch', required=True)

# This is an optional flag that is only used by an external user outside of the
# results-collection project.
parser.add_argument('--no-timestamps', action='store_true', default=False,
                    help='set when reports do not have timestamps '
                         '(time_start & time_end)')

if __name__ == '__main__':
    main(**vars(parser.parse_args()))
