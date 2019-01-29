# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
import six.moves.BaseHTTPServer
import cgi
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
import zlib

here = os.path.dirname(os.path.abspath(__file__))
upload_bin = os.path.sep.join(
    [here, '..', 'src', 'scripts', 'upload-wpt-results.py']
)
default_run_info = {
    u'product': u'firefox',
    u'bits': 64,
    u'has_sandbox': True,
    u'stylo': False,
    u'e10s': True,
    u'headless': False,
    u'os_version': u'16.04',
    u'linux_distro': u'Ubuntu',
    u'browser_version': u'61.0a1',
    u'version': u'Ubuntu 16.04',
    u'debug': False,
    u'os': u'linux',
    u'processor': u'x86_64',
    u'revision': u'503a4f322c662853f7956700830b37cf3f84390e'
}


class Handler(six.moves.BaseHTTPServer.BaseHTTPRequestHandler):
    def log_message(*argv):
        pass

    def do_POST(self):
        body_length = int(self.headers['Content-Length'])
        content_type = cgi.parse_header(self.headers['Content-Type'])

        if content_type[0] == 'multipart/form-data':
            body = cgi.parse_multipart(self.rfile, content_type[1])
            body['result_file'] = zlib.decompress(
                body['result_file'][0], zlib.MAX_WBITS | 16
            )
        else:
            body = str(self.rfile.read(body_length))

        self.server.requests.append({
            'headers': self.headers,
            'payload': body
        })

        self.send_response(self.server.status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


def make_results():
    return {
        '1_of_2.json': {
            'time_start': 1,
            'time_end': 1,
            'run_info': dict(default_run_info),
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
            'time_start': 1,
            'time_end': 1,
            'run_info': dict(default_run_info),
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

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
        except OSError:
            pass

        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()

    def upload(self, product, browser_channel, browser_version, os_name,
               os_version, results_dir, results, port, override_platform,
               total_chunks, git_branch, no_timestamps=False):
        for filename in results:
            with open(os.path.join(results_dir, filename), 'w') as handle:
                json.dump(results[filename], handle)

        cmd = [
            upload_bin, '--raw-results-directory', results_dir,
            '--product', product,
            '--browser-channel', browser_channel,
            '--browser-version', browser_version,
            '--os', os_name,
            '--os-version', os_version,
            '--url', 'http://localhost:%s' % port,
            '--user-name', 'fake-name',
            '--secret', 'fake-secret',
            '--override-platform', override_platform,
            '--total-chunks', str(total_chunks),
            '--git-branch', git_branch
        ]
        if no_timestamps:
            cmd.append('--no-timestamps')

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        return (proc.returncode, stdout, stderr)

    def assertBasicAuth(self, authorization, name, password):
        parts = authorization.split(' ')
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], 'Basic')
        self.assertEqual(parts[1].decode('base64'), '%s:%s' % (name, password))

    def assertReport(self, json_data, expected_data):
        expected_results = expected_data['results']
        expected_metadata = dict(expected_data)
        del expected_metadata['results']
        actual_data = json.loads(json_data)
        actual_results = actual_data['results']
        actual_metadata = dict(actual_data)
        del actual_metadata['results']

        self.assertEqual(actual_metadata, expected_metadata)
        self.assertItemsEqual(actual_results, expected_results)

    def start_server(self, port):
        self.server = six.moves.BaseHTTPServer.HTTPServer(('', port), Handler)
        self.server.status_code = 201
        self.server.requests = []

        def target(server):
            server.serve_forever()

        self.server_thread = threading.Thread(
            target=target, args=(self.server,)
        )

        self.server_thread.start()

    def test_basic(self):
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('firefox',
                                                 'stable',
                                                 '2.0',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 9801,
                                                 override_platform='false',
                                                 total_chunks=2,
                                                 git_branch='master')

        self.assertEqual(returncode, 0, stderr)

        requests = self.server.requests

        self.assertEqual(len(requests), 1)
        self.assertBasicAuth(
            requests[0]['headers']['Authorization'], 'fake-name', 'fake-secret'
        )
        self.assertItemsEqual(
            requests[0]['payload']['labels'][0].split(','),
            ['stable', 'master']
        )
        self.assertReport(requests[0]['payload']['result_file'], {
            u'time_start': 1,
            u'time_end': 1,
            u'run_info': default_run_info,
            u'results': [
                {
                    u'test': u'/js/bitwise-or-2.html',
                    u'status': u'OK',
                    u'subtests': []
                },
                {
                    u'test': u'/js/bitwise-or.html',
                    u'status': u'OK',
                    u'subtests': []
                },
                {
                    u'test': u'/js/bitwise-and.html',
                    u'status': u'OK',
                    u'subtests': [
                        {
                            u'status': u'FAIL',
                            u'message': u'bad',
                            u'name': u'first'
                        },
                        {
                            u'status': u'FAIL',
                            u'message': u'bad',
                            u'name': u'second'
                        }
                    ]
                },
            ]
        })

    def test_alternate_branch(self):
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('firefox',
                                                 'stable',
                                                 '2.0',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 9801,
                                                 override_platform='false',
                                                 total_chunks=2,
                                                 git_branch='jelly-doughnut')

        self.assertEqual(returncode, 0, stderr)

        requests = self.server.requests

        self.assertEqual(len(requests), 1)
        self.assertBasicAuth(
            requests[0]['headers']['Authorization'], 'fake-name', 'fake-secret'
        )
        self.assertItemsEqual(
            requests[0]['payload']['labels'][0].split(','),
            ['stable', 'jelly-doughnut']
        )

    def test_consolidate_duration(self):
        results = make_results()
        results['1_of_2.json']['time_start'] = 50
        results['1_of_2.json']['time_end'] = 400
        results['2_of_2.json']['time_start'] = 10
        results['2_of_2.json']['time_end'] = 300
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('firefox',
                                                 'stable',
                                                 '2.0',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 results,
                                                 9801,
                                                 override_platform='false',
                                                 total_chunks=2,
                                                 git_branch='master')

        self.assertEqual(returncode, 0, stderr)

        requests = self.server.requests

        self.assertEqual(len(requests), 1)
        self.assertBasicAuth(
            requests[0]['headers']['Authorization'], 'fake-name', 'fake-secret'
        )
        self.assertItemsEqual(
            requests[0]['payload']['labels'][0].split(','),
            ['stable', 'master']
        )
        self.assertReport(requests[0]['payload']['result_file'], {
            u'time_start': 10,
            u'time_end': 400,
            u'run_info': default_run_info,
            u'results': [
                {
                    u'test': u'/js/bitwise-or-2.html',
                    u'status': u'OK',
                    u'subtests': []
                },
                {
                    u'test': u'/js/bitwise-or.html',
                    u'status': u'OK',
                    u'subtests': []
                },
                {
                    u'test': u'/js/bitwise-and.html',
                    u'status': u'OK',
                    u'subtests': [
                        {
                            u'status': u'FAIL',
                            u'message': u'bad',
                            u'name': u'first'
                        },
                        {
                            u'status': u'FAIL',
                            u'message': u'bad',
                            u'name': u'second'
                        }
                    ]
                },
            ]
        })

    def test_insert_platform(self):
        self.maxDiff = None
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('chrome',
                                                 'stable',
                                                 '66.0',
                                                 'windows',
                                                 '95',
                                                 self.temp_dir,
                                                 make_results(),
                                                 9801,
                                                 override_platform='true',
                                                 total_chunks=2,
                                                 git_branch='master')

        self.assertEqual(returncode, 0, stderr)

        expected_run_info = dict(default_run_info)
        expected_run_info[u'product'] = u'chrome'
        expected_run_info[u'browser_version'] = u'66.0'
        expected_run_info[u'os'] = u'windows'
        expected_run_info[u'os_version'] = u'95'

        requests = self.server.requests

        self.assertEqual(len(requests), 1)
        self.assertBasicAuth(
            requests[0]['headers']['Authorization'], 'fake-name', 'fake-secret'
        )
        self.assertItemsEqual(
            requests[0]['payload']['labels'][0].split(','),
            ['stable', 'master']
        )
        self.assertReport(requests[0]['payload']['result_file'], {
            u'time_start': 1,
            u'time_end': 1,
            u'run_info': expected_run_info,
            u'results': [
                {
                    u'test': u'/js/bitwise-or-2.html',
                    u'status': u'OK',
                    u'subtests': []
                },
                {
                    u'test': u'/js/bitwise-or.html',
                    u'status': u'OK',
                    u'subtests': []
                },
                {
                    u'test': u'/js/bitwise-and.html',
                    u'status': u'OK',
                    u'subtests': [
                        {
                            u'status': u'FAIL',
                            u'message': u'bad',
                            u'name': u'first'
                        },
                        {
                            u'status': u'FAIL',
                            u'message': u'bad',
                            u'name': u'second'
                        }
                    ]
                },
            ]
        })

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
                                                 port=9804,
                                                 override_platform='false',
                                                 total_chunks=2,
                                                 git_branch='master')

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
                                                 port=9802,
                                                 override_platform='false',
                                                 total_chunks=2,
                                                 git_branch='master')

        self.assertNotEqual(returncode, 0, stdout)

    def test_missing_results(self):
        self.start_server(9802)
        partial_results = make_results()
        del partial_results['1_of_2.json']
        returncode, stdout, stderr = self.upload('firefox',
                                                 'stable',
                                                 '1.0.1',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 partial_results,
                                                 total_chunks=2,
                                                 override_platform='false',
                                                 port=9802,
                                                 git_branch='master')

        self.assertNotEqual(returncode, 0, stdout)
        self.assertEqual(len(self.server.requests), 0)

    def test_missing_timestamps(self):
        self.start_server(9802)
        results = make_results()
        del results['1_of_2.json']['time_start']
        returncode, stdout, stderr = self.upload('firefox',
                                                 'stable',
                                                 '1.0.1',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 results,
                                                 total_chunks=2,
                                                 override_platform='false',
                                                 port=9802,
                                                 git_branch='master')

        self.assertNotEqual(returncode, 0, stdout)
        self.assertEqual(len(self.server.requests), 0)

    def test_no_timestamps(self):
        self.start_server(9802)
        results = make_results()
        del results['1_of_2.json']['time_start']
        del results['1_of_2.json']['time_end']
        del results['2_of_2.json']['time_start']
        del results['2_of_2.json']['time_end']
        returncode, stdout, stderr = self.upload('firefox',
                                                 'stable',
                                                 '1.0.1',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 results,
                                                 total_chunks=2,
                                                 override_platform='false',
                                                 port=9802,
                                                 git_branch='master',
                                                 no_timestamps=True)

        self.assertEqual(returncode, 0, stderr)

        requests = self.server.requests

        self.assertEqual(len(requests), 1)
        self.assertBasicAuth(
            requests[0]['headers']['Authorization'], 'fake-name', 'fake-secret'
        )
        self.assertItemsEqual(
            requests[0]['payload']['labels'][0].split(','),
            ['stable', 'master']
        )
        self.assertReport(requests[0]['payload']['result_file'], {
            u'run_info': default_run_info,
            u'results': [
                {
                    u'test': u'/js/bitwise-or-2.html',
                    u'status': u'OK',
                    u'subtests': []
                },
                {
                    u'test': u'/js/bitwise-or.html',
                    u'status': u'OK',
                    u'subtests': []
                },
                {
                    u'test': u'/js/bitwise-and.html',
                    u'status': u'OK',
                    u'subtests': [
                        {
                            u'status': u'FAIL',
                            u'message': u'bad',
                            u'name': u'first'
                        },
                        {
                            u'status': u'FAIL',
                            u'message': u'bad',
                            u'name': u'second'
                        }
                    ]
                },
            ]
        })


if __name__ == '__main__':
    unittest.main()
