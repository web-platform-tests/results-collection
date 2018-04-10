# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from buildbot.plugins import steps
from buildbot.plugins import util


class WptRunStep(steps.ShellCommand):
    name = util.Interpolate(
        'WPT Run ' +
        '(%(prop:browser_name)s, %(prop:this_chunk)s of %(prop:total_chunks)s)'
    )

    def __init__(self, *args, **kwargs):
        kwargs['name'] = self.name
        kwargs['command'] = self.makeWptRunCommand

        super(WptRunStep, self).__init__(*args, **kwargs)

    @staticmethod
    @util.renderer
    def makeWptRunCommand(properties):
        browser_id = None
        browser_name = properties.getProperty('browser_name')
        command = [
            './wpt', 'run',
            '--install-fonts',
            '--log-wptreport', properties.getProperty('log_wptreport'),
            '--log-raw', properties.getProperty('log_raw'),
            '--this-chunk', properties.getProperty('this_chunk'),
            '--total-chunks', properties.getProperty('total_chunks')
        ]

        if properties.getProperty('use_sauce_labs'):
            if browser_name == 'edge':
                sauce_browser_name = 'MicrosoftEdge'
            else:
                sauce_browser_name = browser_name

            browser_id = util.Interpolate(
                'sauce:%(kw:sauce_browser_name)s:%(prop:browser_version)s',
                sauce_browser_name=sauce_browser_name
            )
            sauce_platform_id = util.Interpolate(
                '%(prop:os_name)s %(prop:os_version)s'
            )

            command.extend([
                '--sauce-platform', sauce_platform_id,
                '--sauce-user', util.Interpolate('%(secret:sauce_labs_user)s'),
                '--sauce-key', util.Interpolate('%(secret:sauce_labs_key)s'),
                '--sauce-tunnel-id', properties.getProperty('workername'),
                '--sauce-connect-binary', 'sc',
                '--no-restart-on-unexpected',
                '--run-by-dir', '3'
            ])
        else:
            command = ['xvfb-run', '--auto-servernum'] + command

            command.extend([
                '--binary', properties.getProperty('browser_binary')
            ])

            browser_id = browser_name

        if browser_name == 'firefox':
            # temporary fix to allow WebRTC tests to call getUserMedia
            command.extend([
                '--setpref', 'media.navigator.streams.fake=true'
            ])
        elif browser_name == 'chrome':
            # This is intended as a temporary fix to allow the webrtc tests in
            # Chrome to call getUserMedia without failing out.
            command.extend([
                '--binary-arg=--use-fake-ui-for-media-stream',
                '--binary-arg=--use-fake-device-for-media-stream'
            ])

        command.append(browser_id)

        return command
