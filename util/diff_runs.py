#!/usr/bin/env python

# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

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
from itertools import ifilter
from urllib import urlencode
from typing import List

# Relative imports
here = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(here, '../run/'))
from run_summary import TestRunSpec, TestRunSummary, TestRunSummaryDiff  # noqa


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
    parser.add_argument(
        'tests',
        type=str,
        nargs='*',
        metavar='test',
        help='Test paths to filter by')
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
            specBefore = TestRunSpec(self.args.before.sha,
                                     self.args.before.platforms[i])
            specAfter = TestRunSpec(self.args.after.sha,
                                    self.args.after.platforms[i])
            runBefore = self.fetcher.fetchResults(specBefore)
            if runBefore is None:
                self.logger.warning('Failed to fetch %s' % specBefore)

            runAfter = self.fetcher.fetchResults(specAfter)
            if runAfter is None:
                self.logger.warning('Failed to fetch %s' % specAfter)

            self.logger.info('Diffing %s and %s...' % (specBefore, specAfter))

            if runBefore is None or runAfter is None:
                continue

            diff = self.diff_results_summaries(runBefore, runAfter)
            diff.print_summary(self.logger)

    def diff_results_summaries(self,
                               run_before,  # type: TestRunSummary
                               run_after,   # type: TestRunSummary
                               ):
        # type: (TestRunSummary, TestRunSummary) -> TestRunSummaryDiff
        assert run_before is not None and run_after is not None
        if hasattr(self.args, 'tests'):
            self.cull_ignored_tests(run_before.summary, self.args.tests)
            self.cull_ignored_tests(run_after.summary, self.args.tests)

        differences = 0
        checked = 0
        added = 0
        removed = 0

        tests = run_before.summary.keys()
        for test in filter(lambda x: x not in run_after.summary, tests):
            removed += 1

        for test in run_after.summary.keys():
            checked += 1

            if test not in run_before.summary:
                added += 1
                continue

            resultAfter = run_after.summary[test]
            resultBefore = run_before.summary[test]

            passingDelta = resultAfter[0] - resultBefore[0]
            totalDelta = resultAfter[1] - resultBefore[1]

            if totalDelta > 0:
                self.logger.info('%s has %d new tests (total)'
                                 % (test, totalDelta))
            elif totalDelta < 0:
                self.logger.info('%s has %d removed tests (total)'
                                 % (test, math.fabs(totalDelta)))

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
        return TestRunSummaryDiff(
            run_before=run_before,
            run_after=run_after,
            added=added,
            deleted=removed,
            changed=differences,
            total=checked)

    def cull_ignored_tests(self, results, testWhitelist):
        if testWhitelist is None or len(testWhitelist) < 1:
            return

        # Cull tests that aren't whitelisted.
        culled = 0
        keys = results.keys()
        tests = len(keys)
        for key in keys:
            def match(x): return key.startswith(x)
            if next(ifilter(match, testWhitelist), None) is None:
                culled += 1
                del results[key]
        self.logger.debug(
            'Culled %d ignored tests of %d total' % (culled, tests))


class Fetcher(object):
    '''Fetcher is a placeholder class which wraps request-logic, for stubbing
    'fetchResults' output for the unit tests.'''

    def __init__(self):
        self.pool = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())

    def fetchResults(self, spec):  # type: (TestRunSpec) -> TestRunSummary
        '''Fetch a python object representing the test run results JSON for the
        given sha/platform spec. '''
        # type: (str, str) -> dict
        # Note that the dict's keys are the test paths, and values are an
        # array of [pass_count, total_test_count].
        # For example JSON output, see https://wpt.fyi/results?platform=chrome

        encodedArgs = urlencode({'sha': spec.sha, 'platform': spec.platform})
        url = 'https://wpt.fyi/results?' + encodedArgs

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
        return TestRunSummary(spec, json.loads(response.data.decode('utf-8')))


if __name__ == '__main__':
    main()
