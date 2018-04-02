# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from buildbot.plugins import steps, util


class WPTChunkedStep(steps.Trigger):
    def __init__(self, platform_id, platform, total_chunks, *args, **kwargs):
        self.platform_id = platform_id
        self.platform = platform
        self.total_chunks = total_chunks

        kwargs['name'] = str('Trigger %s chunks on %s' % (
            total_chunks, platform['browser_name'].title()
        ))

        super(WPTChunkedStep, self).__init__(*args, **kwargs)

    def getSchedulersAndProperties(self):
        spec = []
        revision = self.build.properties.getProperty('got_revision')
        revision_date = self.build.properties.getProperty('revision_date')
        browser_name = self.platform['browser_name']
        results_id = '%s-%s-%s' % (browser_name, revision, self.build.buildid)

        for scheduler in self.schedulerNames:
            unimportant = scheduler in self.unimportantSchedulerNames

            for this_chunk in range(1, self.total_chunks + 1):
                spec.append({
                    'sched_name': scheduler,
                    'props_to_set': {
                        'this_chunk': this_chunk,
                        'total_chunks': self.total_chunks,
                        'platform_id': self.platform_id,
                        'browser_name': browser_name,
                        'browser_version': self.platform['browser_version'],
                        'os_name': self.platform['os_name'],
                        'os_version': self.platform['os_version'],
                        'use_sauce_labs': self.platform.get('sauce', False),
                        'revision_date': revision_date,
                        'results_id': results_id
                    },
                    'unimportant': unimportant
                })

        return spec
