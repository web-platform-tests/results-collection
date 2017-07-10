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
