#!/usr/bin/env python

# Copyright 2018 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
from datetime import datetime
import httplib
import json
import logging
import os
import re
import subprocess
import tempfile
import urlparse
import urllib


def main(product, channel, os_name, bucket_name):
    '''Find the most recent build of a given browser and provide a stable URL
    from which it may be downloaded. Because browser vendors do not necessarily
    commit to hosting outdated builds, this may involve downloading the build
    and persisting it to an internally-managed object storage location.'''

    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    logging.basicConfig(level='INFO', format=log_format)
    logger = logging.getLogger('get-browser-url')

    source_url = None

    logger.info('Locating artifact for %s browser', product.title())

    if product == 'firefox':
        source_url = locate_firefox(channel)
    elif product == 'chrome':
        source_url = locate_chrome(channel)

    if source_url is None:
        raise Exception('Unable to locate the requested artifact')

    logger.info('Artifact located at %s', source_url)

    directory = '%s-%s-%s' % (product, channel, os_name)
    identifier = get_identifier(source_url)
    uri = '%s/%s/%s' % (bucket_name, directory, identifier)

    url = get_mirrored(uri)

    if url is None:
        logger.info('Unable to find mirrored version. Mirroring...')

        mirror(source_url, uri)

        url = get_mirrored(uri)

    assert url is not None

    logger.info('Mirrored version found at %s', url)

    return url


def locate_firefox(channel):
    if channel == 'experimental':
        product = 'firefox-nightly-latest-ssl'
    else:
        product = 'firefox-latest-ssl'

    url = ('https://download.mozilla.org/?product=%s&os=linux64&lang=en-US' %
           product)

    return head_request(url).getheader('Location')


def locate_chrome(channel):
    if channel == 'experimental':
        release_name = 'unstable_current'
    else:
        release_name = 'stable_current'

    return ('https://dl.google.com/linux/direct/google-chrome-%s_amd64.deb' %
            release_name)


def head_request(url):
    parts = urlparse.urlparse(url)
    conn = httplib.HTTPConnection(parts.netloc)
    path = parts.path
    if parts.query:
        path += '?%s' % parts.query
    conn.request('HEAD', path)
    return conn.getresponse()


def get_identifier(source_artifact_url):
    response = head_request(source_artifact_url)
    etag = response.getheader('etag')
    return re.match('"?([^"]*)"?', etag).groups()[0]


def get_mirrored(uri):
    mirrored = 'https://storage.googleapis.com/%s' % uri
    response = head_request(mirrored)

    if response.status >= 200 and response.status < 300:
        return mirrored


def mirror(source_artifact_url, uri):
    artifact_file = tempfile.mkstemp()[1]
    metadata_file = tempfile.mkstemp()[1]

    try:
        opener = urllib.URLopener()
        opener.retrieve(source_artifact_url, artifact_file)
        metadata = {
            'url': source_artifact_url,
            'date': str(datetime.utcnow()),
        }

        with open(metadata_file, 'w') as handle:
            json.dump(metadata, handle)

        subprocess.check_call([
            'gsutil', 'cp', artifact_file, 'gs://%s' % uri
        ])
        subprocess.check_call([
            'gsutil', 'cp', metadata_file, 'gs://%s.json' % uri
        ])
    finally:
        os.remove(artifact_file)
        os.remove(metadata_file)


parser = argparse.ArgumentParser(description=main.__doc__)
parser.add_argument('--product',
                    choices=('firefox', 'chrome'),
                    required=True)
parser.add_argument('--channel',
                    choices=('stable', 'experimental'),
                    required=True)
parser.add_argument('--os-name',
                    choices=('linux',),
                    required=True)
parser.add_argument('--bucket-name',
                    required=True)


if __name__ == '__main__':
    print main(**vars(parser.parse_args()))
