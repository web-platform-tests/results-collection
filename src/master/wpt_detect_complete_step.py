# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

from buildbot.plugins import steps
from twisted.python import log
from twisted.internet import defer


class WptDetectCompleteStep(steps.Trigger):
    def __init__(self, dir_name, *args, **kwargs):
        kwargs['doStepIf'] = self.allResultsPresent
        self.dir_name = dir_name

        super(WptDetectCompleteStep, self).__init__(*args, **kwargs)

    @defer.inlineCallbacks
    def allResultsPresent(self, step):
        total_chunks = self.build.properties.getProperty('total_chunks')

        dir_name = yield self.dir_name.getRenderingFor(self.build.properties)

        actual = set(os.listdir(dir_name))
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

        defer.returnValue(len(missing) == 0)
