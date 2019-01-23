#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
import argparse
import contextlib
import httplib
import json
import logging
import time
import urlparse


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def request(method, url):
    parts = urlparse.urlparse(url)
    if parts.scheme == 'https':
        Connection = httplib.HTTPSConnection
    else:
        Connection = httplib.HTTPConnection
    conn = Connection(parts.netloc)
    path = parts.path
    if parts.query:
        path += '?%s' % parts.query

    headers = {'User-Agent': 'wpt-results-collector'}

    conn.request(method, path, headers=headers)

    yield conn.getresponse()

    conn.close()


@contextlib.contextmanager
def get_with_retry(url, interval, timeout):
    try:
        with request('GET', url) as response:
            status = response.status
            message = 'HTTP Error %s: %s' % (status, response.reason)

            if status >= 200 and status < 300:
                yield response
                return
    except Exception as exception:
        message = str(exception)

    remaining = timeout - interval

    if remaining <= 0:
        logger.warn('Retry timeout exceeded.')
        raise Exception(message)

    logging.warn(message)
    logging.warn('Retrying in %s seconds...' % (interval,))

    time.sleep(interval)

    with get_with_retry(url, interval, remaining) as response:
        yield response


def main(interval, retry_interval, retry_timeout):
    '''Query the wpt.fyi "revision announcer" for the latest revision of
    interest as published at the specified interval. Documentation available
    online at https://github.com/web-platform-tests/wpt.fyi/'''

    url = 'https://wpt.fyi/api/revisions/latest'

    with get_with_retry(url, retry_interval, retry_timeout) as response:
        body = response.read()

        try:
            data = json.loads(body)
        except ValueError:
            raise ValueError(
                'Unable to parse response as JSON: "%s"' % body
            )

    try:
        return data['revisions'][interval]['hash']
    except (KeyError, TypeError):
        raise ValueError(
            'Unable to access `revisions.%s.hash` in response:\n%s' % (
                interval, body
            )
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--retry-interval',
                        type=int,
                        default=60,
                        help='''Duration in seconds to wait between retrying
                            failed requests to wpt.fyi'''
                        )
    parser.add_argument('--retry-timeout',
                        type=int,
                        default=60 * 10,
                        help='''Duration in seconds to wait before cancelling
                            attempts to retry failed requests'''
                        )
    parser.add_argument('interval',
                        choices=('hourly', 'two_hourly', 'six_hourly',
                                 'twelve_hourly', 'daily', 'weekly'))

    print(main(**vars(parser.parse_args())))
