# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import BaseHTTPServer
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

here = os.path.dirname(os.path.abspath(__file__))
gsutil_stub_dir = os.path.sep.join([here, 'bin-stubs'])
gsutil_stub_args = os.path.sep.join([gsutil_stub_dir, 'gsutil_args.json'])
gsutil_stub_content = os.path.sep.join([gsutil_stub_dir, 'content-to-upload'])
upload_bin = os.path.sep.join(
    [here, '..', 'src', 'scripts', 'upload-wpt-results.py']
)


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def log_message(*argv):
        pass

    def do_POST(self):
        body_length = int(self.headers['Content-Length'])
        self.server.requests.append({
            'path': self.path,
            'body': str(self.rfile.read(body_length))
        })
        self.send_response(self.server.status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


def make_results():
    return {
        '1_of_2.json': {
            'results': [
                {
                    'test': '/js/bitwise-or.html',
                    'status': 'OK',
                    'subtests': []
                },
                {
                    'test': '/js/bitwise-and.html',
                    'status': 'OK',
                    'subtests': [
                        {'status': 'FAIL', 'message': 'bad', 'name': 'first'},
                        {'status': 'FAIL', 'message': 'bad', 'name': 'second'}
                    ]
                }
            ]
        },
        '2_of_2.json': {
            'results': [
                {
                    'test': '/js/bitwise-or-2.html',
                    'status': 'OK',
                    'subtests': []
                }
            ]
        }
    }


class TestUploadWptResults(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.server = None

        # gsutil "stub" output files and directories will only be present if
        # the tests were run previously
        try:
            os.remove(gsutil_stub_args)
        except OSError:
            pass

        try:
            shutil.rmtree(gsutil_stub_content)
        except OSError:
            pass

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
        except OSError:
            pass

        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()

    def upload(self, browser_name, browser_channel, browser_version, os_name,
               os_version, results_dir, results, port, gsutil_return_code=0):
        env = dict(os.environ)
        env['PATH'] = gsutil_stub_dir + os.pathsep + os.environ['PATH']
        env['GSUTIL_RETURN_CODE'] = str(gsutil_return_code)

        for filename in results:
            with open(os.path.join(results_dir, filename), 'w') as handle:
                json.dump(results[filename], handle)

        proc = subprocess.Popen([
            upload_bin, '--raw-results-directory', results_dir,
            '--platform-id', '%s-%s-%s-%s' % (browser_name, browser_version,
                                              os_name, os_version),
            '--browser-name', browser_name,
            '--browser-channel', browser_channel,
            '--browser-version', browser_version,
            '--os-name', os_name,
            '--os-version', os_version,
            '--wpt-revision', '1234567890abcdef',
            '--wpt-revision-date', '2018-03-19T17:54:32-04:00',
            '--bucket-name', 'wpt-test',
            '--notify-url', 'http://localhost:%s' % port,
            '--notify-secret', 'fake-secret'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()

        return (proc.returncode, stdout, stderr)

    def assertJsonFiles(self, dir_name, data):
        for filename in data:
            path = os.path.sep.join([dir_name] + filename.split('/'))

            with gzip.open(path) as handle:
                self.assertEqual(data[filename], json.loads(handle.read()))

    def start_server(self, port):
        self.server = BaseHTTPServer.HTTPServer(('', port), Handler)
        self.server.status_code = 201
        self.server.requests = []

        def target(server):
            server.serve_forever()

        self.server_thread = threading.Thread(
            target=target, args=(self.server,)
        )

        self.server_thread.start()

    def test_basic_firefox(self):
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('firefox',
                                                 'stable',
                                                 '2.0',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 9801)

        self.assertEqual(returncode, 0, stderr)

        self.assertJsonFiles(gsutil_stub_content, {
            'firefox-2.0-linux-4.0-summary.json.gz': {
                '/js/bitwise-and.html': [1, 3],
                '/js/bitwise-or-2.html': [1, 1],
                '/js/bitwise-or.html': [1, 1]
            },
            'firefox-2.0-linux-4.0/js/bitwise-and.html': {
                'test': '/js/bitwise-and.html',
                'status': 'OK',
                'subtests': [
                    {u'message': 'bad', 'name': 'first', 'status': 'FAIL'},
                    {u'message': 'bad', 'name': 'second', 'status': 'FAIL'}
                ]
            },
            'firefox-2.0-linux-4.0/js/bitwise-or.html': {
                'test': '/js/bitwise-or.html',
                'status': 'OK',
                'subtests': []
            },
            'firefox-2.0-linux-4.0/js/bitwise-or-2.html':  {
                'test': '/js/bitwise-or-2.html',
                'status': u'OK',
                'subtests': []
            }
        })
        self.assertEqual(len(self.server.requests), 1)
        request = self.server.requests[0]
        self.assertEqual(request['path'], '/?secret=fake-secret')
        self.assertEqual(json.loads(request['body']), {
            'browser_name': 'firefox',
            'browser_version': '2.0',
            'commit_date': '2018-03-19T17:54:32-04:00',
            'os_name': 'linux',
            'os_version': '4.0',
            'results_url': 'https://storage.googleapis.com/' +
                               'wpt-test/1234567890/' +
                               'firefox-2.0-linux-4.0-summary.json.gz',
            'revision': '1234567890'
        })

    def test_basic_chrome(self):
        self.start_server(9802)
        returncode, stdout, stderr = self.upload('chrome',
                                                 'stable',
                                                 '4.3.2',
                                                 'macos',
                                                 '10.5',
                                                 self.temp_dir,
                                                 make_results(),
                                                 port=9802)

        self.assertEqual(returncode, 0, stderr)

        self.assertJsonFiles(gsutil_stub_content, {
            'chrome-4.3.2-macos-10.5-summary.json.gz': {
                '/js/bitwise-and.html': [1, 3],
                '/js/bitwise-or-2.html': [1, 1],
                '/js/bitwise-or.html': [1, 1]
            },
            'chrome-4.3.2-macos-10.5/js/bitwise-and.html': {
                'test': '/js/bitwise-and.html',
                'status': 'OK',
                'subtests': [
                    {u'message': 'bad', 'name': 'first', 'status': 'FAIL'},
                    {u'message': 'bad', 'name': 'second', 'status': 'FAIL'}
                ]
            },
            'chrome-4.3.2-macos-10.5/js/bitwise-or.html': {
                'test': '/js/bitwise-or.html',
                'status': 'OK',
                'subtests': []
            },
            'chrome-4.3.2-macos-10.5/js/bitwise-or-2.html':  {
                'test': '/js/bitwise-or-2.html',
                'status': u'OK',
                'subtests': []
            }
        })
        self.assertEqual(len(self.server.requests), 1)
        request = self.server.requests[0]
        self.assertEqual(request['path'], '/?secret=fake-secret')
        self.assertEqual(json.loads(request['body']), {
            'browser_name': 'chrome',
            'browser_version': '4.3.2',
            'commit_date': '2018-03-19T17:54:32-04:00',
            'os_name': 'macos',
            'os_version': '10.5',
            'results_url': 'https://storage.googleapis.com/' +
                               'wpt-test/1234567890/' +
                               'chrome-4.3.2-macos-10.5-summary.json.gz',
            'revision': '1234567890'
        })

    def test_experimental(self):
        self.start_server(9802)
        returncode, stdout, stderr = self.upload('chrome',
                                                 'experimental',
                                                 '4.3.2',
                                                 'macos',
                                                 '10.5',
                                                 self.temp_dir,
                                                 make_results(),
                                                 port=9802)

        self.assertEqual(returncode, 0, stderr)

        self.assertJsonFiles(gsutil_stub_content, {
            'chrome-4.3.2-macos-10.5-summary.json.gz': {
                '/js/bitwise-and.html': [1, 3],
                '/js/bitwise-or-2.html': [1, 1],
                '/js/bitwise-or.html': [1, 1]
            },
            'chrome-4.3.2-macos-10.5/js/bitwise-and.html': {
                'test': '/js/bitwise-and.html',
                'status': 'OK',
                'subtests': [
                    {u'message': 'bad', 'name': 'first', 'status': 'FAIL'},
                    {u'message': 'bad', 'name': 'second', 'status': 'FAIL'}
                ]
            },
            'chrome-4.3.2-macos-10.5/js/bitwise-or.html': {
                'test': '/js/bitwise-or.html',
                'status': 'OK',
                'subtests': []
            },
            'chrome-4.3.2-macos-10.5/js/bitwise-or-2.html':  {
                'test': '/js/bitwise-or-2.html',
                'status': u'OK',
                'subtests': []
            }
        })
        self.assertEqual(len(self.server.requests), 1)
        request = self.server.requests[0]
        self.assertEqual(request['path'], '/?secret=fake-secret')
        self.assertEqual(json.loads(request['body']), {
            'browser_name': 'chrome-experimental',
            'browser_version': '4.3.2',
            'commit_date': '2018-03-19T17:54:32-04:00',
            'os_name': 'macos',
            'os_version': '10.5',
            'results_url': 'https://storage.googleapis.com/' +
                               'wpt-test/1234567890/' +
                               'chrome-4.3.2-macos-10.5-summary.json.gz',
            'revision': '1234567890'
        })

    def test_expand_foreign_platform(self):
        self.start_server(9802)
        returncode, stdout, stderr = self.upload('chrome',
                                                 'stable',
                                                 '4.3.2',
                                                 'beos',
                                                 '*',
                                                 self.temp_dir,
                                                 make_results(),
                                                 port=9802)

        self.assertNotEqual(returncode, 0, stdout)
        self.assertEqual(len(self.server.requests), 0)

    def test_failed_request(self):
        self.start_server(9804)
        self.server.status_code = 500
        returncode, stdout, stderr = self.upload('chrome',
                                                 'stable',
                                                 '4.3.2',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 port=9804)

        self.assertNotEqual(returncode, 0, stdout)
        self.assertEqual(len(self.server.requests), 1)

    def test_no_server(self):
        returncode, stdout, stderr = self.upload('chrome',
                                                 'stable',
                                                 '4.3.2',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 port=9802)

        self.assertNotEqual(returncode, 0, stdout)

    def test_failed_gsutil(self):
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('chrome',
                                                 'stable',
                                                 '3.2.1',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 port=9801,
                                                 gsutil_return_code=1)

        self.assertEqual(returncode, 1, stdout)
        self.assertEqual(len(self.server.requests), 0)

    def test_duplicated_results(self):
        self.start_server(9802)
        duplicated_results = make_results()
        duplicated_results['2_of_2.json']['results'].append(
            duplicated_results['1_of_2.json']['results'][0]
        )
        returncode, stdout, stderr = self.upload('firefox',
                                                 'stable',
                                                 '1.0.1',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 duplicated_results,
                                                 port=9801)

        self.assertEqual(returncode, 1, stdout)
        self.assertFalse(os.access(gsutil_stub_content, os.R_OK))
        self.assertEqual(len(self.server.requests), 0)


if __name__ == '__main__':
    unittest.main()
