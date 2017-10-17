#!/usr/bin/env python3

import datetime
import json
import os

from github import Github
from google.cloud import storage


REPO_NAME = 'w3c/web-platform-tests'
GCP_PROJECT = 'wptdashboard'
RESULTS_BUCKET = 'wptd'


def main():
    g = Github("jeffcarp", os.environ.get('GH_TOKEN').strip())

    start = datetime.datetime(2017, 10, 1)
    commits = []
    for commit in g.get_repo(REPO_NAME).get_commits(since=start):
        commits.append({
            'api_commit': commit,
            'sha': commit.sha,
            'message': commit.commit.message,
            'commit_date': commit.commit.committer.date.isoformat(),
            'testruns': []
        })

    # Get all SHAs from GCS bucket
    # Match each WPT commit with the WPTD commit

    storage_client = storage.Client(project=GCP_PROJECT)
    bucket = storage_client.get_bucket(RESULTS_BUCKET)
    sha_directories = list_directory(bucket)

    for sha_directory in sha_directories:
        sha = sha_directory.replace('/', '')

        for index, commit in enumerate(commits):
            if commit['api_commit'].sha.startswith(sha):
                testrun_paths = list_directory(bucket, prefix='%s/' % sha)
                commits[index]['testruns'].extend([
                    path[11:-1] for path in testrun_paths
                ])

    # Delete api_commits from commits
    for index, commit in enumerate(commits):
        del commits[index]['api_commit']

    filename = 'wpt-shas-testruns.json'
    blob = bucket.blob(filename)
    blob.upload_from_string(json.dumps(commits), content_type='application/json')

    print('Uploaded!')
    print('https://storage.googleapis.com/wptd/%s' % filename)


def list_directory(bucket, prefix=None):
    iterator = bucket.list_blobs(delimiter='/', prefix=prefix)
    response = iterator._get_next_page_response()
    return response['prefixes']


if __name__ == '__main__':
    main()
