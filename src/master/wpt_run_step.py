# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from buildbot.plugins import steps
from buildbot.plugins import util
import os


class WptRunStep(steps.ShellCommand):
    name = util.Interpolate(
        'WPT Run ' +
        '(%(prop:browser_name)s, %(prop:this_chunk)s of %(prop:total_chunks)s)'
    )

    def __init__(self, *args, **kwargs):
        kwargs['name'] = self.name
        kwargs['command'] = self.makeWptRunCommand
        kwargs['logfiles'] = {
            'sauce-connect-log': {
                'filename': '/var/log/sauce-connect/sc.log',
                'follow': True
            },
            'xvfb-log': {
                'filename': '/var/log/xvfb/xvfb.log',
                'follow': True
            }
        }

        super(WptRunStep, self).__init__(*args, **kwargs)

    @staticmethod
    @util.renderer
    def makeWptRunCommand(properties):
        browser_id = None
        browser_name = properties.getProperty('browser_name')
        command = [
            'run-and-verify.py',
            '--max-attempts', properties.getProperty('max_attempts'),
            '--log-wptreport', properties.getProperty('log_wptreport'),
            '--log-raw', properties.getProperty('log_raw'),
            '--',
            '--log-mach', '-',
            '--this-chunk', properties.getProperty('this_chunk'),
            '--total-chunks', properties.getProperty('total_chunks')
        ]

        if properties.getProperty('use_sauce_labs'):
            workername = properties.getProperty('workername')
            # The key name is derived from the name of the worker. Because the
            # Buildbot "secret" functionality is itself built on Python's
            # string interpolation syntax, the key name must be defined using
            # string concatenation.
            key = util.Interpolate(
                '%(secret:sauce_labs_key_' + workername + ')s'
            )

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
                '--sauce-user', 'wpt-%s' % workername,
                '--sauce-key', key,
                '--sauce-tunnel-id', properties.getProperty('workername'),
                '--sauce-connect-binary', 'sc',
                '--sauce-connect-arg=--logfile=/var/log/sauce-connect/sc.log',
                '--sauce-init-timeout', '45',
                '--no-restart-on-unexpected',
                '--run-by-dir', '3'
            ])
        else:
            if browser_name != 'safari':
                command = [
                    'xvfb-run', '--auto-servernum', '--error-file',
                    '/var/log/xvfb/xvfb.log'
                ] + command

                # The WPT CLI does not support specifying a path to the Safari
                # binary. However, if the corresponding WebDriver binary is
                # used, then that process will launch Safari Technology
                # Preview.
                command.extend([
                    '--binary', properties.getProperty('browser_binary')
                ])

            command.extend([
                '--webdriver-binary',
                properties.getProperty('webdriver_binary'),
                '--install-fonts',
                # The authenticity of results collected in "headless" mode is
                # disputed.
                '--no-headless'
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

            if properties.getProperty('browser_channel') == 'experimental':
                command.append(
                    '--binary-arg=--enable-experimental-web-platform-features'
                )

        command.append(browser_id)

        return command
