# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import BaseHTTPServer
import json
import threading
import urllib2


class HTTPStubber(object):
    '''An HTTP server which forwards errors raised during request handling to
    the main thread.'''
    class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
        def log_message(*argv):
            pass

        def do_GET(self):
            return self.do()

        def do_POST(self):
            return self.do()

        def do(self):
            stubber = self.server.stubber

            try:
                stubber.on_request(self)
            except Exception as e:
                # In order to make test failure messages more intuitive,
                # exceptions raised during command processing should be caught
                # and reported to the main thread (where they can be
                # subsequently re-raised).
                stubber.exception = e
                stubber._exception_lock.release()

    def __init__(self, port=0):
        self._server = BaseHTTPServer.HTTPServer(('', port), self.Handler)
        self._server.stubber = self
        self._exception_lock = threading.Lock()
        self._exception_lock.acquire()

        self.exception = None

    def on_request(self, http_handler):
        http_handler.send_response(200, 'OK')
        http_handler.end_headers()

    @property
    def port(self):
        return self._server.server_port

    def stop(self):
        self._server.shutdown()

    def start(self):
        '''Run the server and block until `stop` is invoked or until an
        exception is raised during HTTP request handling.'''

        def interrupt_on_exception(stubber):
            exception = stubber._exception_lock.acquire()
            stubber.stop()
        threading.Thread(target=interrupt_on_exception, args=(self,)).start()

        # The following call will block until the `stop` method is invoked,
        # either explicitly by the user or as a result of an exception being
        # raised during request handling.
        self._server.serve_forever(0.1)

        if self.exception:
            raise self.exception
        else:
            # If no exception is present, the server was stopped via an
            # external call to the `stop` method, and the thread dedicated to
            # detecting exceptions is still waiting. Release the lock so that
            # thread exits cleanly.
            self._exception_lock.release()
