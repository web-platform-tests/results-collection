# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import os
import subprocess
import sys
import threading
import urllib2

import http_stubber


def decode_cli_arguments(arguments_string):
    '''Parse a string representing a set of command-line arguments.'''

    return json.loads(urllib2.unquote(arguments_string).decode('utf8'))


def encode_cli_arguments(arguments_list):
    '''Prepare a set of command-line arguments (implemented as a list of string
    values) for transmission via HTTP as a URL query string parameter.'''

    return urllib2.quote(json.dumps(arguments_list).encode('utf8'))


def request_and_execute(name, args):
    '''Request instructions from a local HTTP server. Intended for use within
    isolated processes that are acting as "stubs".'''
    try:
        home_port = os.environ['HOME_PORT']
    except KeyError:
        raise Exception(
            'This utility requires that the HOME_PORT environment variable ' +
            'is set.'
        )

    arg_string = encode_cli_arguments(args)
    url = 'http://localhost:%s/%s?%s' % (home_port, name, arg_string)
    response = urllib2.urlopen(url).read()

    instructions = json.loads(response) or {}

    stdout = instructions.get('stdout')
    if stdout is not None:
        sys.stdout.write(stdout)

    stderr = instructions.get('stderr')
    if stderr is not None:
        sys.stderr.write(stderr)

    returncode = instructions.get('returncode')
    if returncode is not None:
        sys.exit(returncode)


class CommandStubber(http_stubber.HTTPStubber):
    def __init__(self):
        super(CommandStubber, self).__init__()
        self.commands = {}

    def on_request(self, http_handler):
        parts = http_handler.path.split('?')
        command_name = parts[0][1:]
        args = decode_cli_arguments(parts[1])

        command = self.commands.get(command_name)
        if command is None:
            raise KeyError(
                'The "%s" commmand was invoked, ' % command_name +
                'but no handler has been defined for it.'
            )

        command['arguments'].append(args)
        instructions = command['handler'](*args)

        http_handler.send_response(200, 'OK')
        http_handler.end_headers()
        http_handler.wfile.write(json.dumps(instructions))

    def add_handler(self, command_name, fn):
        self.commands[command_name] = {
            'handler': fn,
            'arguments': []
        }

    def arguments_for(self, command_name):
        return self.commands[command_name]['arguments']

    def run(self, *args, **kwargs):
        env = kwargs.get('env', dict(os.environ))
        env['HOME_PORT'] = str(self.port)
        kwargs['env'] = env

        proc = subprocess.Popen(*args, **kwargs)
        result = []

        def communicate(proc):
            stdoutdata, stderrdata = proc.communicate()
            result.extend([proc.returncode, stdoutdata, stderrdata])
            self.stop()

        threading.Thread(target=communicate, args=(proc,)).start()

        try:
            self.start()
        finally:
            if proc.poll() is None:
                proc.kill()

        return result
