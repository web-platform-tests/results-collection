#!/usr/bin/python3

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from google.cloud import storage

"""
Scans all WPT results directories and generates an index.

You must be logged into gcloud to run this script. The non-public permission
necessary to generate this index is `bucket.list_blobs`.
"""

GCP_PROJECT = 'wptdashboard'
RESULTS_BUCKET = 'wptd'


def main():
    storage_client = storage.Client(project=GCP_PROJECT)
    bucket = storage_client.get_bucket(RESULTS_BUCKET)
    by_sha = {}
    by_platform = {}

    iterator = bucket.list_blobs(delimiter="/")
    response = iterator._get_next_page_response()
    sha_directories = response['prefixes']

    for sha_directory in sha_directories:
        sha = sha_directory.replace('/', '')
        iterator = bucket.list_blobs(delimiter="/", prefix=sha_directory)
        response = iterator._get_next_page_response()
        platform_directories = [
            prefix[len(sha_directory):].replace('/', '')
            for prefix in response['prefixes']]

        for platform in platform_directories:
            by_sha.setdefault(sha, [])
            by_sha[sha].append(platform)

            by_platform.setdefault(platform, [])
            by_platform[platform].append(sha)

    print('by_sha', by_sha)
    print('by_platform', by_platform)

    index = {
        'by_sha': by_sha,
        'by_platform': by_platform
    }

    filename = 'testruns-index.json'
    blob = bucket.blob(filename)
    blob.upload_from_string(json.dumps(index), content_type='application/json')

    print('Uploaded!')
    print('https://storage.googleapis.com/wptd/%s' % filename)

if __name__ == '__main__':
    main()
