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

import requests

"""
Attempts to approximate the "interoperable subset of the web."

TODO more exposition
"""

INDEX_URL = 'https://storage.googleapis.com/wptd/testruns-index.json'


def main():
    # get latest testrun summary for each platform
    # hm this will be difficult to do at a subtest level, maybe start at the testfile level
    # filter all test files only for those that pass on all platforms
    # what percentage of total testruns is it?

    # index = requests.get(INDEX_URL).json()
    # print(index)
    test_runs = [
        {'revision': 'dd44fd07c5', 'platform_id': 'safari-10-macos-10.12'},
        {'revision': 'b12daf6ead', 'platform_id': 'edge-15-windows-10-sauce'},
        {'revision': 'fd56faf446', 'platform_id': 'firefox-56.0-linux'},
        {'revision': 'fd56faf446', 'platform_id': 'chrome-61.0-linux'},
    ]
    results = {}
    test_files = {}

    for test_run in test_runs:
        url = 'https://storage.googleapis.com/wptd/%s/%s-summary.json.gz' % (
            test_run['revision'], test_run['platform_id']
        )
        print('URL', url)
        test_file_summary = requests.get(url).json()

        print('platform', test_run['platform_id'], 'files', len(test_file_summary.keys()))

        for test_file, results in test_file_summary.items():
            test_files.setdefault(test_file, {})
            test_files[test_file][test_run['platform_id']] = results

    test_files_passing = 0

    for test_file, platform_results in test_files.items():
        if len(platform_results) != len(test_runs):
            # print('Unequal number of results:', test_file, len(platform_results))
            continue

        if all([result[0] == result[1] for result in platform_results.values()]):
            # print('ALL PASSING!', test_file)
            test_files_passing += 1

    print('Test files passing:', test_files_passing)
    print('Test files total:', len(test_files))
    print('Percent of interoperable web:', test_files_passing / len(test_files))


if __name__ == '__main__':
    main()
