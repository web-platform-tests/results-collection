# [web-platform-tests dashboard](https://wpt.fyi/) 📈 [![Build Status](https://travis-ci.org/w3c/wptdashboard.svg?branch=master)](https://travis-ci.org/w3c/wptdashboard)

A dashboard of cross-browser results for [web-platform-tests](https://github.com/w3c/web-platform-tests).

It consists of 3 parts:

- **Running**: VMs scheduled to [run tests locally and on Sauce](run/run.py) daily
- **Serving**: An [App Engine app](main.go) for storing test run metadata and serving HTML
- **Visualizing**: [Polymer elements](components/wpt-results.html) for loading and visualizing test results

## Running locally

You'll need the [Google App Engine Go SDK](https://cloud.google.com/appengine/docs/standard/go/download).

```sh
# Start the server on localhost:8080
dev_appserver.py .
curl http://localhost:8080/tasks/populate-dev-data
```

See [CONTRIBUTING.md](/CONTRIBUTING.md) for more information on local development.

## Running the tests

We run the tests with a Python script [`run/run.py`](run/run.py) which is a thin wrapper around WPT's [`wpt run`](https://github.com/w3c/web-platform-tests/#running-tests-automatically). If you're triaging test failures, use `wpt run`.

### Setup

This will build dependencies and start the Google App Engine development server inside `wptd-dev-instance`.
You'll also need to populate the app datastore with some initial data, using util/populate_dev_data.py.

```sh
./util/populate_dev_data.py \
    --server localhost:9999 \
    --sdk-root /path/to/google-cloud-sdk \
    --creds ~/Downloads/wptdashboard-creds-file.json
```

Further instructions on using the populate util can be found with the --help flag.

See [CONTRIBUTING.md](/CONTRIBUTING.md) for more information on local development.

## Running the tests

We run the tests in the development environment with a Python script [`run/run.py`](run/run.py) which is a thin wrapper around WPT's [`wpt run`](https://github.com/w3c/web-platform-tests/#running-tests-automatically). If you're triaging test failures, use `wpt run`.

### Running

You'll need to make sure that you have Python 2.7 installed. It is recommended that you setup a [virtualenv](https://virtualenv.pypa.io/en/stable/). When you have activated your `virtualenv`, install the dependencies:

```sh
pip install -r requirements.txt
```

Copy the file `run/running.example.ini` to `run/running.ini` and edit the fields to the correct locations for items on your machine. If you do not do this you will receive an error.

To run a directory of WPT, pass the [platform ID](#platform-id) and a test path:

```sh
./run/run.py firefox-56.0-linux --path battery-status
```

# Filesystem and network output

- This script will only write files under `config['build_path']`.
- One run will write approximately 111MB to the filesystem.
- If --upload is specified, it will upload that 111MB of results to GCS.
- To upload results, you must be logged in with `gcloud` in the `wptdashboard` project.

## Using the data

All test result data is public. There are two types of gzipped JSON data files we store: test run summary files, and individual test result files.

### Test run summary files

These are of the pattern: `{sha[0:10]}/{platform_id}-summary.json.gz`

- `sha[0:10]`: the first 10 characters of the WPT commit hash that run was tested against
- `platform_id`: the key of the platform configuration in `browsers.json`

Example: https://storage.googleapis.com/wptd/791e95323d/firefox-56.0-linux-summary.json.gz

(Note that `wptd` is the bucket name)

Structure:
An object where the key is the test file name and the value is a list of the type
`[number passing subtests, total number subtests]`.

```json
{
    "/test/file/name1.html": [0, 1],
    "/test/file/name2.html": [5, 10]
}
```

### Individual test result files

These are of the pattern: `{sha[0:10]}/{platform_id}/{test_file_path}`

- `sha[0:10]`: the first 10 characters of the WPT commit hash that run was tested against
- `platform_id`: the key of the platform configuration in `browsers.json`
- `test_file_path`: the full WPT path of the test file

Example: https://storage.googleapis.com/wptd/b12daf6ead/safari-10-macos-10.12-sauce/IndexedDB/abort-in-initial-upgradeneeded.html

Structure:
```json
{
    "test": "/test/file/name.html",
    "status": "OK",
    "message": "The failure message, if exists",
    "subtests": [
        {
            "status": "FAIL",
            "name": "The subtest name",
            "message": "The failure message, if exists"
        }
    ]
}
```

### Large-scale analysis

There is no public API for TestRuns, so if you need to access only the most recent results, looking at
the main page will give you the latest test SHAs. If you need to access earlier results, an
exhaustive search is the only way to do that (see issue [#73](https://github.com/w3c/wptdashboard/issues/73) and [#43](https://github.com/w3c/wptdashboard/issues/43)).

## Miscellaneous

#### WPT documentation page for each browser

- Chromium: https://chromium.googlesource.com/chromium/src/+/master/docs/testing/web_platform_tests.md
- Firefox: https://wiki.mozilla.org/Auto-tools/Projects/web-platform-tests
- WebKit: https://trac.webkit.org/wiki/WebKitW3CTesting

#### Location of the WPT in each browser’s source tree

- Chromium: [`src/third_party/WebKit/LayoutTests/imported/wpt`](https://cs.chromium.org/chromium/src/third_party/WebKit/LayoutTests/external/wpt/)
- Firefox: [`testing/web-platform/tests`](https://dxr.mozilla.org/mozilla-central/source/testing/web-platform/tests)
- WebKit: [`LayoutTests/imported/w3c/web-platform-tests`](https://trac.webkit.org/browser/trunk/LayoutTests/imported/w3c/web-platform-tests)

#### You can run almost any WPT test on w3c-test.org

Try out http://w3c-test.org/html/semantics/forms/the-input-element/checkbox.html

This doesn't work with some HTTPS tests. Also be advised that the server is not intended for frequent large-scale test runs.

#### Sources of inspiration

- ECMAScript 6 compatibility table - https://kangax.github.io/compat-table/es6/
- https://html5test.com/

# Appendix

## Terminology

### Platform ID

These are the keys in [`browsers.json`](browsers.json). They're used to identify a tuple (browser name, browser version, os name, os version).
