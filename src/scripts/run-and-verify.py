#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import json
import logging
import os
import subprocess
import sys
import threading


def main(max_attempts, log_wptreport, log_raw, wpt_args):
    '''Execute web-platform-tests repeatedly until results have been collected
    for all of the expected tests.'''

    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level='INFO', format=log_format)
    logger = logging.getLogger('validate-wpt-results')
    is_complete = False
    current_attempt = 0

    if len(wpt_args) > 0 and wpt_args[0] == '--':
        wpt_args.pop(0)

    while not is_complete and current_attempt < max_attempts:
        current_attempt += 1

        logger.info('Attempt %s of %s' % (current_attempt, max_attempts))

        wpt_run(logger, log_wptreport, log_raw, wpt_args)

        normalize_wpt_report(log_wptreport)

        try:
            completeness = analyze(log_wptreport, log_raw)
        except Exception as e:
            logger.info('Error: %s', e)
            continue

        incorrect_count = 0

        logger.info('Expected %s results' % completeness['total_expected'])
        logger.info('Found %s results' % completeness['total_actual'])

        for x in ('unexpected', 'missing'):
            count = len(completeness[x])
            incorrect_count += count

            logger.info('Found %s %s results' % (count, x))

            for test_name in completeness[x]:
                logger.info('- %s' % test_name)

        log_allowed_missing(logger, completeness)

        is_complete = incorrect_count == 0

    if not is_complete:
        try:
            os.remove(log_wptreport)
        except Exception:
            pass

        raise Exception(
            'Failed to collect complete results after %s attempts' % (
                max_attempts
            )
        )


def wpt_run(logger, log_wptreport, log_raw, wpt_args):
    command = ['python', './wpt', 'run']
    command.extend(['--log-raw', log_raw, '--log-wptreport', log_wptreport])
    command.extend(wpt_args)

    logger.info('Invoking the WPT CLI with the following command:')
    logger.info('    %s', ' '.join(command))
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    log_streams('wpt-run', proc, logger)

    proc.wait()

    logger.info('WPT CLI exited with return code %s' % proc.returncode)


def log_streams(command_name, proc, logger):
    def target(cmd_name, stream_name, stream, logger):
        prefix = '%s:%s ' % (cmd_name, stream_name)

        with stream:
            for line in iter(stream.readline, b''):
                logger.info(prefix + line.rstrip())

    threading.Thread(
        target=target, args=(command_name, 'stdout', proc.stdout, logger)
    ).start()

    threading.Thread(
        target=target, args=(command_name, 'stderr', proc.stderr, logger)
    ).start()


def normalize_wpt_report(log_wptreport):
    '''The WPT CLI is known to produce invalid JSON files in some
    circumstances [1]. These cases represent test executions with zero results.
    Tolerate this condition by creating a valid report describing that
    condition.

    [1] https://github.com/w3c/web-platform-tests/issues/9481'''
    try:
        with open(log_wptreport) as handle:
            json.load(handle)
    except (IOError, ValueError):
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

    raise ValueError(
        'Unable to identify expected number of tests from log file: %s' % (
            log_raw
        )
    )


def get_actual_results(log_wptreport):
    with open(log_wptreport) as handle:
        data = json.load(handle)

        assert isinstance(data, dict)
        assert isinstance(data.get('results'), list)

        return set([result['test'] for result in data.get('results')])


def analyze(log_wptreport, log_raw):
    expected_results = get_expected_results(log_raw)
    actual_results = get_actual_results(log_wptreport)

    # A regression in WPT caused the "raw log" to include tests which are never
    # executed:
    #
    # https://github.com/web-platform-tests/wpt/issues/12366
    #
    # This logic and the `log_allowed_missing` function have been implemented
    # as a workaround for that behavior. The workaround assumes that all
    # invalid tests have names that end in ".js" and that no valid tests have
    # names which satisfy that criteria.
    #
    # This is a partial solution because the true heuristic depends on the test
    # contents. The effort required to implement and test a complete solution
    # is not warranted because the upstream bug has been acknowledged, and a
    # correction is under review.
    #
    # This logic should be removed when the regression has been fixed.
    allowed_missing = set()
    for expected in expected_results:
        if expected.endswith('.js'):
            allowed_missing.add(expected)
    expected_results -= allowed_missing

    return {
        'total_expected': len(expected_results),
        'total_actual': len(actual_results),
        'unexpected': actual_results - expected_results,
        'allowed_missing': allowed_missing,
        'missing': expected_results - actual_results
    }


def log_allowed_missing(logger, completeness):
    count = len(completeness['allowed_missing'])

    logger.info('Found %s allowed missing results' % (count))

    for test_name in completeness['allowed_missing']:
        logger.info('- %s' % test_name)


parser = argparse.ArgumentParser(description=main.__doc__)

parser.add_argument('--max-attempts', type=int, required=True)
parser.add_argument('--log-wptreport', required=True)
parser.add_argument('--log-raw', required=True)
parser.add_argument('wpt_args', nargs=argparse.REMAINDER)

if __name__ == '__main__':
    main(**vars(parser.parse_args()))
