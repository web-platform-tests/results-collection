# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from buildbot.plugins import steps, util


def prefix(filename):
    return util.Interpolate('%(prop:temporary_directory)s/' + filename)


class CreateStep(steps.SetPropertyFromCommand):
    '''Platform-agnostic Buildbot step for creating a temporary filesystem'''

    def __init__(self, *args, **kwargs):
        kwargs['property'] = 'temporary_directory'
        kwargs['command'] = [
          'python', '-c', 'import tempfile; print tempfile.mkdtemp()'
        ]

        super(CreateStep, self).__init__(*args, **kwargs)


class RemoveStep(steps.ShellCommand):
    '''Platform-agnostic Buildbot step for deleting a temporary filesystem
    directory as created by `CreateStep`.'''

    code = 'import shutil; shutil.rmtree("%(prop:temporary_directory)s")'

    def __init__(self, *args, **kwargs):
        kwargs['command'] = ['python', '-c', util.Interpolate(self.code)]

        super(RemoveStep, self).__init__(*args, **kwargs)
