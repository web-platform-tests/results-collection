#!/usr/bin/env python

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

"""
Tool for pulling 2 results JSON blobs for given runs, and diffing the results.

Example usage:
./diff_runs.py \
    --before=chrome@b952881825 \
    --after=chrome@7a0cf8ade7
"""

import argparse
import certifi
import inspect
import json
import logging
import math
import os
import sys
import urllib3

from urllib import urlencode
from typing import List

here = os.path.dirname(__file__)

def main():
    args = parse_flags()  # type: argparse.Namespace

    loggingLevel = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=loggingLevel)
    logger = logging.getLogger()

    if sys.version_info < (2, 7, 11):
        # SSL requests fail for earlier versions (e.g. 2.7.6)
        logger.fatal('python version 2.7.11 or greater required')
        return

    differ = RunDiffer(args, logger, Fetcher())
    differ.diff()


# Create an ArgumentParser for the flags we'll expect.
def parse_flags():  # type: () -> argparse.Namespace
    # Re-use the docs above as the --help output.
    parser = argparse.ArgumentParser(description=inspect.cleandoc(__doc__))
    desc = (
        '{platform(s)}@{sha} where platform(s) is a comma separated list of '
        'platforms, e.g. \'chrome,safari\', and sha is SHA[0:10] of the run '
        'to compare against the initial run.'
        'Note that order is important, e.g.'
        '--before=foo,bar --after=baz,qux'
        'will compare foo:baz, and bar:qux.'
    )
    parser.add_argument(
        '--before',
        required=True,
        type=PlatformsAtRevision.parse,
        help=desc)
    parser.add_argument(
        '--after',
        required=True,
        type=PlatformsAtRevision.parse,
        help=desc)
    parser.add_argument(
        '--log',
        type=str,
        default='INFO',
        help='Log level to output')
    namespace = parser.parse_args()

    # Check the before and after platform lists have the same length.
    if len(namespace.before.platforms) != len(namespace.after.platforms):
        msg = ('Different number of platforms in before and after flags.\n'
               '--before %s\n--after %s')

        raise ValueError(msg
                         % (namespace.before.platforms,
                            namespace.after.platforms))

    return namespace


class PlatformsAtRevision(object):
    def __init__(self, sha, platforms):  # type: (str, List[str]) -> None
        self.sha = sha
        self.platforms = platforms

    @classmethod
    def parse(cls, value):  # type: (str) -> PlatformsAtRevision
        pieces = value.split('@')
        sha = 'latest'
        platforms = ['chrome', 'edge', 'firefox', 'safari']
        if len(pieces) > 2:
            raise ValueError(value)

        if len(pieces) > 1:
            sha = pieces[1]
        elif len(pieces) > 0:
            sha = pieces[0]

        if len(pieces) > 1:
            platforms = pieces[0].split(',')

        return PlatformsAtRevision(sha, platforms)


class RunDiffer(object):
    def __init__(self,
                 args,  # type: argparse.Namespace
                 logger,  # type: logging.Logger
                 fetcher  # type: Fetcher
                 ):
        self.args = args
        self.logger = logger
        self.fetcher = fetcher

    def diff(self):
        beforeSHA = self.args.before.sha  # type: str
        afterSHA = self.args.after.sha  # type: str

        for i in range(0, len(self.args.after.platforms)):
            specBefore = '%s@%s' % (self.args.before.platforms[i],
                                    self.args.before.sha)
            specAfter = '%s@%s' % (self.args.after.platforms[i],
                                   self.args.after.sha)
            runBefore = self.fetcher.fetchResults(
                beforeSHA, self.args.before.platforms[i])
            runAfter = self.fetcher.fetchResults(
                afterSHA, self.args.after.platforms[i])

            self.logger.info('Diffing %s and %s...' % (specBefore, specAfter))

            if runBefore is None:
                self.logger.warning('Failed to fetch %s' % specBefore)
            if runAfter is None:
                self.logger.warning('Failed to fetch %s' % specAfter)
            if runBefore is None or runAfter is None:
                continue

            differences = 0
            checked = 0
            added = 0
            removed = 0

            for k in filter(lambda x: x not in runAfter, runBefore.keys()):
                removed += 1

            for test in runAfter.keys():
                checked += 1

                if test not in runBefore:
                    added += 1
                    continue

                resultAfter = runAfter[test]
                resultBefore = runBefore[test]

                passingDelta = resultAfter[0] - resultBefore[0]
                totalDelta = resultAfter[1] - resultBefore[1]

                if totalDelta > 0:
                    self.logger.info('%s has %d new tests (total)'
                                     % (test, totalDelta))
                elif totalDelta < 0:
                    self.logger.info('%s has %d removed tests (total)')

                if passingDelta < 0:
                    self.logger.warning('%s has %d new failures'
                                        % (test, math.fabs(passingDelta)))
                elif passingDelta > 0:
                    self.logger.info('%s has %d new passes'
                                     % (test, passingDelta))

                delta = math.fabs(totalDelta) + math.fabs(passingDelta)
                logging.debug('%s has %d differences (%s vs %s)'
                              % (test,
                                 passingDelta,
                                 resultAfter,
                                 resultBefore))
                differences += delta

            self.logger.info(
                'Finished diff of %s and %s with %d differences in %d tests'
                % (specBefore, specAfter, differences, checked))
            if (added > 0):
                self.logger.info('%d tests ran in %s but not in %s'
                                 % (added, specAfter, specBefore))
            if (removed > 0):
                self.logger.info('%d tests ran in %s but not in %s'
                                 % (removed, specBefore, specAfter))


class Fetcher(object):
    '''Fetcher is a placeholder class which wraps request-logic, for stubbing
    'fetchResults' output for the unit tests.'''

    def __init__(self):
        self.pool = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())

    def fetchResults(self, sha, platform):
        '''Fetch a python object representing the test run results JSON for the
        given sha/platform spec. '''
        # type: (str, str) -> object
        # Note that the object's keys are the test paths, and values are an
        # array of [pass_count, total_test_count].
        # For example JSON output, see https://wpt.fyi/json?platform=chrome

        encodedArgs = urlencode({'sha': sha, 'platform': platform})
        url = 'https://wpt.fyi/json?' + encodedArgs

        try:
            response = self.pool.request('GET', url, redirect=False)
        except urllib3.exceptions.SSLError as e:
            logging.warning('SSL error fetching %s: %s' % (url, e.message))
            return None

        if response.status // 100 != 3:
            logging.warning(
                'Got unexpected non-redirect result %d for url %s'
                % (response.status, url))
            return None

        loadedUrl = response.headers['location']
        response = self.pool.request('GET', loadedUrl)

        if response.status != 200:
            logging.warning('Failed to fetch %s' % (url))
            return None

        logging.debug('Processing JSON from %s' % (url))
        return json.loads(response.data.decode('utf-8'))


if __name__ == '__main__':
    main()
