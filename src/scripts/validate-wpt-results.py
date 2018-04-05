#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import json
import logging

THRESHOLD = 0.02


def main(log_wptreport, log_raw):
    '''Verify that the test results for a trial of the Web Platform Tests (as
    described by the WPT CLI's `--log-wptreport` feature) includes information
    for all the tests that were run (as described by the WPT CLI's `--log-raw`
    feature). Permit a limited number of missing and/or unexpected test
    results. Extend the test results with a object-valued property named
    "completeness" which defines the following integer properties:
    "total_expected", "total_unexpected", "total_missing".'''

    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level='INFO', format=log_format)
    logger = logging.getLogger('validate-wpt-results')

    normalize_wpt_report(log_wptreport)

    expected_results = get_expected_results(log_raw)
    actual_results = get_actual_results(log_wptreport)

    unexpected_results = actual_results - expected_results
    missing_results = expected_results - actual_results

    logger.info('Expected %s results' % len(expected_results))
    logger.info('Found %s results' % len(actual_results))

    logger.info('%s unexpected results' % len(unexpected_results))
    for result in unexpected_results:
        logger.info('- %s' % result)

    logger.info('%s missing results' % len(missing_results))
    for result in missing_results:
        logger.info('- %s' % result)

    total_incorrect = len(unexpected_results) + len(missing_results)
    total_expected = len(expected_results)

    annotate(log_wptreport, len(expected_results), len(unexpected_results),
             len(missing_results))

    # Due to the way tests are segmented (i.e. the WPT CLI's "chunk"
    # functionality), a results set may be empty. If the "raw" log describes
    # this state, then an empty results set should be accepted.
    if total_expected == 0:
        assert total_incorrect == 0
    else:
        assert float(total_incorrect) / total_expected < THRESHOLD, (
            'Percentage of incorrect results exceeded threshold'
        )


def normalize_wpt_report(log_wptreport):
    '''The WPT CLI is known to produce invalid JSON files in some
    circumstances [1]. These cases represent test executions with zero results.
    Tolerate this condition by creating a valid report describing that
    condition.

    [1] https://github.com/w3c/web-platform-tests/issues/9481'''
    try:
        with open(log_wptreport) as handle:
            json.load(handle)
    except IOError, ValueError:
        with open(log_wptreport, 'w') as handle:
            json.dump({'results': []}, handle)


def get_expected_results(log_raw):
    '''Retrieve a list of strings which define all tests available in a given
    Web Platform Test repository. This number is distinct from the number of
    test files due to the presence of "multi-global" tests.'''
    with open(log_raw) as handle:
        for line in handle:
            try:
                data = json.loads(line)
            except ValueError:
                continue

            assert isinstance(data, dict)

            if data.get('action') != 'suite_start':
                continue

            assert isinstance(data.get('tests'), dict)
            assert isinstance(data['tests'].get('default'), list)

            return set(data['tests']['default'])

    return set()


def get_actual_results(log_wptreport):
    with open(log_wptreport) as handle:
        data = json.load(handle)

        assert isinstance(data, dict)
        assert isinstance(data.get('results'), list)

        return set([result['test'] for result in data.get('results')])


def annotate(log_wptreport, total_expected, total_unexpected, total_missing):
    '''Extend a file describing Web Platform Tests results with an object
    property named "completeness" which specifies the expected and actual
    number of tests described by the report.'''
    with open(log_wptreport) as handle:
        data = json.load(handle)

    data['completeness'] = {
        'total_expected': total_expected,
        'total_unexpected': total_unexpected,
        'total_missing': total_missing
    }

    with open(log_wptreport, 'w') as handle:
        json.dump(data, handle)


parser = argparse.ArgumentParser(description=main.__doc__)
parser.add_argument('--log-wptreport', required=True)
parser.add_argument('--log-raw', required=True)

if __name__ == '__main__':
    main(**vars(parser.parse_args()))
