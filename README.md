# [web-platform-tests dashboard](https://wptdashboard.appspot.com/) 📈

A dashboard of cross-browser results for [web-platform-tests](https://github.com/w3c/web-platform-tests).

It consists of 2 parts:

- An App Engine app for ingesting, organizing, and serving test results - see [`main.go`](main.go)
- Running infrastructure

## Running locally

You'll need the [Google App Engine Go SDK](https://cloud.google.com/appengine/docs/standard/go/download).

```sh
# Start the server on localhost:8080
dev_appserver .
```

See [CONTRIBUTING.md](/CONTRIBUTING.md) for more information on local development.

## Using the data

All test result data is public. There are two types of gzipped JSON data files we store.

### Test run summary files

These are of the pattern: `{sha[0:10]}/{platform_id}-summary.json.gz`

- `sha[0:10]` - the first 10 characters of the WPT SHA that run was tested against
- `platform_id` - the key of the platform configuration in `browsers.json`

Example: https://storage.googleapis.com/wptd/791e95323d/firefox-56.0-linux-summary.json.gz

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

- `sha[0:10]` - the first 10 characters of the WPT SHA that run was tested against
- `platform_id` - the key of the platform configuration in `browsers.json`
- `test_file_path` - the full WPT path of the test file

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

There is currently no public API for TestRuns, so if you need to access only the most recent results, looking at
the main page will give you the latest test SHAs. If you need to access earlier results, currently an
exhaustive search is the only way to do that.

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

#### Disclaimer

This is not an official Google product.
