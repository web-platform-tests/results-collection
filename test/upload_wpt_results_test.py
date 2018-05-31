# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import BaseHTTPServer
import cgi
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


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def log_message(*argv):
        pass

    def do_POST(self):
        body_length = int(self.headers['Content-Length'])
        content_type = cgi.parse_header(self.headers['Content-Type'])

        if content_type[0] == 'multipart/form-data':
            body = cgi.parse_multipart(self.rfile, content_type[1])
        else:
            body = str(self.rfile.read(body_length))

        self.server.request_payloads.append(body)

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

    def upload(self, product, browser_version, os_name, os_version,
               results_dir, results, port, total_chunks):
        for filename in results:
            with open(os.path.join(results_dir, filename), 'w') as handle:
                json.dump(results[filename], handle)

        proc = subprocess.Popen([
            upload_bin, '--raw-results-directory', results_dir,
            '--product', product,
            '--browser-version', browser_version,
            '--os', os_name,
            '--os-version', os_version,
            '--url', 'http://localhost:%s' % port,
            '--user-name', 'fake-name',
            '--secret', 'fake-secret',
            '--total-chunks', str(total_chunks)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()

        return (proc.returncode, stdout, stderr)

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
        self.server = BaseHTTPServer.HTTPServer(('', port), Handler)
        self.server.status_code = 201
        self.server.request_payloads = []

        def target(server):
            server.serve_forever()

        self.server_thread = threading.Thread(
            target=target, args=(self.server,)
        )

        self.server_thread.start()

    def test_basic(self):
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('firefox',
                                                 '2.0',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 9801,
                                                 total_chunks=2)

        self.assertEqual(returncode, 0, stderr)

        self.assertEqual(len(self.server.request_payloads), 1)
        self.assertReport(self.server.request_payloads[0]['result_file'][0], {
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

    def test_consolidate_duration(self):
        results = make_results()
        results['1_of_2.json']['time_start'] = 50
        results['1_of_2.json']['time_end'] = 400
        results['2_of_2.json']['time_start'] = 10
        results['2_of_2.json']['time_end'] = 300
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('firefox',
                                                 '2.0',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 results,
                                                 9801,
                                                 total_chunks=2)

        self.assertEqual(returncode, 0, stderr)

        self.assertEqual(len(self.server.request_payloads), 1)
        self.assertReport(self.server.request_payloads[0]['result_file'][0], {
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
        results = make_results()
        self.maxDiff = None
        del results['1_of_2.json']['run_info']['product']
        del results['1_of_2.json']['run_info']['browser_version']
        del results['1_of_2.json']['run_info']['os']
        del results['1_of_2.json']['run_info']['os_version']
        del results['2_of_2.json']['run_info']['product']
        del results['2_of_2.json']['run_info']['browser_version']
        del results['2_of_2.json']['run_info']['os']
        del results['2_of_2.json']['run_info']['os_version']
        self.start_server(9801)
        returncode, stdout, stderr = self.upload('chrome',
                                                 '66.0',
                                                 'windows',
                                                 '95',
                                                 self.temp_dir,
                                                 results,
                                                 9801,
                                                 total_chunks=2)

        self.assertEqual(returncode, 0, stderr)

        expected_run_info = dict(default_run_info)
        expected_run_info[u'product'] = u'chrome'
        expected_run_info[u'browser_version'] = u'66.0'
        expected_run_info[u'os'] = u'windows'
        expected_run_info[u'os_version'] = u'95'

        self.assertEqual(len(self.server.request_payloads), 1)
        self.assertReport(self.server.request_payloads[0]['result_file'][0], {
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
                                                 '4.3.2',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 port=9804,
                                                 total_chunks=2)

        self.assertNotEqual(returncode, 0, stdout)
        self.assertEqual(len(self.server.request_payloads), 1)

    def test_no_server(self):
        returncode, stdout, stderr = self.upload('chrome',
                                                 '4.3.2',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 make_results(),
                                                 port=9802,
                                                 total_chunks=2)

        self.assertNotEqual(returncode, 0, stdout)

    def test_duplicated_results(self):
        self.start_server(9802)
        duplicated_results = make_results()
        duplicated_results['2_of_2.json']['results'].append(
            duplicated_results['1_of_2.json']['results'][0]
        )
        returncode, stdout, stderr = self.upload('firefox',
                                                 '1.0.1',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 duplicated_results,
                                                 total_chunks=2,
                                                 port=9801)

        self.assertEqual(returncode, 1, stdout)
        self.assertEqual(len(self.server.request_payloads), 0)

    def test_missing_results(self):
        self.start_server(9802)
        partial_results = make_results()
        del partial_results['1_of_2.json']
        returncode, stdout, stderr = self.upload('firefox',
                                                 '1.0.1',
                                                 'linux',
                                                 '4.0',
                                                 self.temp_dir,
                                                 partial_results,
                                                 total_chunks=2,
                                                 port=9801)

        self.assertNotEqual(returncode, 0, stdout)
        self.assertEqual(len(self.server.request_payloads), 0)


if __name__ == '__main__':
    unittest.main()
