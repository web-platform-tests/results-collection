# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from buildbot.plugins import steps, util
from six.moves import range


class WPTChunkedStep(steps.Trigger):
    def __init__(self, platform_id, platform, total_chunks, *args, **kwargs):
        self.platform_id = platform_id
        self.platform = platform
        self.total_chunks = total_chunks

        kwargs['name'] = str('Trigger %s chunks on %s@%s' % (
            total_chunks, platform['browser_name'].title(),
            platform['browser_channel']
        ))

        super(WPTChunkedStep, self).__init__(*args, **kwargs)

    def getSchedulersAndProperties(self):
        spec = []
        browser_name = self.platform['browser_name']
        browser_channel = self.platform['browser_channel']
        browser_url = self.build.properties.getProperty(
            'browser_url_%s_%s' % (browser_name, browser_channel)
        )
        webdriver_url = self.build.properties.getProperty(
            'webdriver_url_%s' % browser_name
        )

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
                        'browser_channel': browser_channel,
                        'browser_version': self.platform['browser_version'],
                        'browser_url': browser_url,
                        'webdriver_url': webdriver_url,
                        'os_name': self.platform['os_name'],
                        'os_version': self.platform['os_version'],
                        'use_sauce_labs': self.platform.get('remote')
                    },
                    'unimportant': unimportant
                })

        return spec
