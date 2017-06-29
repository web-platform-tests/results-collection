#!/usr/bin/python3
import json
import requests

from google.cloud import storage

def list_paths(bucket):
    paths = []
    blobs = bucket.list_blobs(prefix='results')
    for blob in blobs:
        # if '/chrome-60.0-debian-8.json.gz' in blob.name:
        if '/firefox-55.0-debian-8.json.gz' in blob.name:
            paths.append(blob.name)
    return paths

def analyze_flakiness():

    # if we have a checkout of WPT we can get the dates for that
    # for the first check we don't need date
    client = storage.Client()
    bucket = client.get_bucket('wptdashboard.appspot.com')
    paths = list_paths(bucket)

    url_base = 'https://storage.googleapis.com/wptdashboard.appspot.com/'
    tests = {}
    dupes = {}
    analyzed_results = 0

    for path in paths:
        print('Fetching path', path)
        blob = bucket.get_blob(path)
        s = blob.download_as_string()
        results = json.loads(s.decode('utf-8'))

        analyzed_results += 1

        for test, result in results.items():
            passing, total = result
            if test in tests:
                prev_passing, prev_total, different = tests[test]
                if total == prev_total and passing != prev_passing:
                    print('Found results that do not match for test', test, 'Previous:', prev_passing, prev_total, 'Current: ', passing, total)
                    # tests[test] = [prev_passing, prev_total, different + 1]
                    if test in dupes:
                        dupes[test] += 1
                    else:
                        dupes[test] = 1

            tests[test] = [passing, total, 0]

    print(analyzed_results, 'analyzed_results')
    print('Top 20 tests sorted by number of instances num total results matched but num passing results differed:')
    for test, num in sorted(dupes.items(), key=lambda i: i[1], reverse=True)[0:30]:
        print(num, test)


if __name__ == '__main__':
    analyze_flakiness()
