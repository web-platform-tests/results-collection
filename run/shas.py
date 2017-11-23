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

import argparse
import logging
import os
import subprocess

from datetime import date, timedelta

"""
shas.py defines methods for determining which SHA to run against on a given
date.
"""


class SHAFinder(object):

    def __init__(self,
                 logger,  # type: logging.Logger
                 date=date.today(),  # type: datetime.date
                 ):
        self.logger = logger
        self.date = date

    def get_todays_sha(self, path):  # type: (str) -> str
        """
        Gets the first SHA for the current date of the git repo in the given
        path.
        """
        today = self.date
        tomorrow = self.date + timedelta(days=1)
        command = [
            'git',
            'log',
            '--format=%H',
            '--after="%s T00:00:00Z"' % today.isoformat(),
            '--before="%s T00:00:00Z"' % tomorrow.isoformat(),
            '--reverse'
        ]
        abspath = os.path.abspath(path)
        self.logger.debug('Using dir ' + abspath)
        self.logger.debug('Executing ' + ' '.join(command))
        output = subprocess.check_output(command, cwd=abspath)
        shas = output.decode('UTF-8').strip().split(os.linesep)
        if len(shas) > 0:
            return shas[0]
        return ''

    def get_head_sha(self, path):  # type: (str) -> str
        """
        Gets the HEAD SHA for the git repo in the given path.
        """
        command = [
            'git',
            'rev-parse',
            'HEAD',
        ]
        abspath = os.path.abspath(path)
        self.logger.debug('Using dir ' + abspath)
        self.logger.debug('Executing ' + ' '.join(command))
        output = subprocess.check_output(command, cwd=abspath)
        sha = output.decode('UTF-8').strip()
        assert len(sha) == 40, 'Invalid SHA: "%s"' % sha
        return sha


if __name__ == '__main__':
    # Re-use the docs above as the --help output.
    parser = argparse.ArgumentParser(
        description="Gets the first SHA of the current date."
    )
    parser.add_argument(
        '--wpt-path',
        required=True,
        dest='wpt_path',
        type=str,
        help="Root path of the w3c/web-platform-tests github project"
    )
    parser.add_argument(
        '--log',
        type=str,
        default='INFO',
        help='Log level to output'
    )
    namespace = parser.parse_args()

    loggingLevel = getattr(logging, namespace.log.upper(), None)
    logging.basicConfig(level=loggingLevel)
    logger = logging.getLogger()

    sha_finder = SHAFinder(logger)
    logger.info('HEAD SHA is %s' % sha_finder.get_head_sha(namespace.wpt_path))
    logger.info('First SHA for %s is %s' %
                (date.today().isoformat(),
                 sha_finder.get_todays_sha(namespace.wpt_path) or '(empty)'))
