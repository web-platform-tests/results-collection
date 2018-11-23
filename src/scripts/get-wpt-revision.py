#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import contextlib
import httplib
import json
import urlparse


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


def main(interval):
    '''Query the wpt.fyi "revision announcer" for the latest revision of
    interest as published at the specified interval. Documentation available
    online at https://github.com/web-platform-tests/wpt.fyi/'''

    with request('GET', 'https://wpt.fyi/api/revisions/latest') as response:
        if response.status < 200 or response.status >= 300:
            raise Exception(
                'HTTP Error %s: %s' % (response.status, response.reason)
            )

        body = response.read()

        try:
            data = json.loads(body)
        except ValueError:
            raise ValueError(
                'Unable to parse response as JSON: "%s"' % body
            )

    try:
        return data['revisions'][interval]['hash']
    except:
        raise ValueError(
            'Unable to access `revisions.%s.hash` in response:\n%s' % (
                interval, body
            )
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('interval',
                        choices=('hourly', 'two_hourly', 'six_hourly',
                                 'twelve_hourly', 'daily', 'weekly'))

    print main(**vars(parser.parse_args()))
