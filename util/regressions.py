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
Tool for parsing a 'wpt run --log-wptreport' output file against a summary in
production, and alerting on any unexpected results.

Example usage:
./regressions.py \
    --before chrome@latest \
    --report ./wptd-{SHA}-{platform}-report.log

"""

import argparse
import inspect
import json
import logging
import os
import sys
from diff_runs import RunDiffer, Fetcher

# Relative imports
here = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(here, '../run/'))
from run import report_to_summary  # noqa
from run_summary import TestRunSpec, TestRunSummary  # noqa


def main():
    args = parse_flags()  # type: argparse.Namespace

    logging_level = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=logging_level)
    logger = logging.getLogger()

    if sys.version_info < (2, 7, 11):
        # SSL requests fail for earlier versions (e.g. 2.7.6)
        logger.fatal('python version 2.7.11 or greater required')
        return

    fetcher = Fetcher()
    run_before = fetcher.fetchResults(args.before)

    report_summary = None
    with open(args.report) as f:
        report = json.load(f)
        assert len(report['results']) > 0, (
            '0 test results, something went wrong, stopping.')
        report_summary = report_to_summary(report)

    differ = RunDiffer(args, logger, fetcher)
    diff = differ.diff_results_summaries(
        run_before,
        TestRunSummary(args.after, report_summary))

    diff.print_summary(logger)


# Create an ArgumentParser for the flags we'll expect.
def parse_flags():  # type: () -> argparse.Namespace
    # Re-use the docs above as the --help output.
    parser = argparse.ArgumentParser(description=inspect.cleandoc(__doc__))
    parser.add_argument(
        '--report',
        required=True,
        type=str,
        help="File path for the wpt report output file.")
    parser.add_argument(
        '--before',
        required=True,
        type=TestRunSpec.parse,
        help='{platform}@{sha} e.g. \'chrome@latest\' for the run to compare'
             ' the report against')
    parser.add_argument(
        '--after',
        type=TestRunSpec.parse,
        help='{platform}@{sha} e.g. \'chrome@latest\' of the run which'
             'produced the report. Defaults to \'local-run@latest\' for'
             'convenience, since local identification is not crucial.',
        default='local-run@latest')
    parser.add_argument(
        '--log',
        type=str,
        default='INFO',
        help='Log level to output')
    namespace = parser.parse_args()

    # Check the before and after platform lists have the same length.
    if not os.path.isfile(namespace.report):
        raise ValueError('Invalid report file.')

    return namespace


if __name__ == '__main__':
    main()
