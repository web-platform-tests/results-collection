# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

from buildbot.plugins import steps
from twisted.python import log


class WptDetectCompleteStep(steps.Trigger):
    def __init__(self, *args, **kwargs):
        kwargs['doStepIf'] = self.allResultsPresent

        super(WptDetectCompleteStep, self).__init__(*args, **kwargs)

    def allResultsPresent(self, step):
        platform_id = self.build.properties.getProperty('platform_id')
        revision = self.build.properties.getProperty('revision')
        total_chunks = self.build.properties.getProperty('total_chunks')
        chunk_results_dir = os.path.sep.join([
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'chunk-results',
            revision,
            platform_id
        ])
        actual = set(os.listdir(chunk_results_dir))
        expected = set(
            [
                '%s_of_%s.json' % (idx, total_chunks)
                for idx in range(1, total_chunks + 1)
            ]
        )
        missing = expected - actual

        log.msg('WptDetectCompleteStep: Missing %s results (expected %s)' % (
            len(missing), len(expected)
        ))

        return len(missing) == 0
