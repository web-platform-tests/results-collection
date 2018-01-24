# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


class TestRunSpec(object):
    def __init__(self, sha, platform):  # type: (str, str) -> None
        self.sha = sha
        self.platform = platform

    @classmethod
    def parse(cls, value):  # type: (str) -> TestRunSpec
        pieces = value.split('@')
        sha = 'latest'
        if len(pieces) > 2 or len(pieces) < 2:
            raise ValueError(value)

        sha = pieces[1]
        platform = pieces[0]

        return TestRunSpec(sha, platform)

    @property
    def spec(self):
        return '%s@%s' % (self.platform, self.sha)

    def __repr__(self):
        return self.spec


class TestRunSummary(object):
    def __init__(self,
                 spec,    # type: TestRunSpec
                 summary  # type: dict
                 ):
        self.spec = spec
        self.summary = summary


class TestRunSummaryDiff(object):
    '''SummaryDiff represents a summary of numbers of the differences between
    two run summaries'''

    def __init__(self,
                 run_before,  # type: TestRunSpec
                 run_after,   # type: TestRunSpec
                 added,       # type: int
                 deleted,     # type: int
                 changed,     # type: int
                 total        # type: int
                 ):
        self.run_before = run_before
        self.run_after = run_after
        self.added = added
        self.deleted = deleted
        self.changed = changed
        self.total = total

    # Alias, for convenience.
    @property
    def removed(self):
        return self.deleted

    def print_summary(self, logger):  # type: (logging.Logger) -> None
        logger.info(
            'Finished diff of %s and %s with %d differences in %d tests'
            % (self.run_before.spec,
               self.run_after.spec,
               self.changed,
               self.total))
        if self.added > 0:
            logger.info('%d tests ran in %s but not in %s'
                        % (self.added,
                           self.run_after.spec,
                           self.run_before.spec))
        if self.removed > 0:
            logger.info('%d tests ran in %s but not in %s'
                        % (self.deleted,
                           self.run_before.spec,
                           self.run_after.spec))
