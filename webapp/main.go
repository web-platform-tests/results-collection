// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package webapp

import (
	"html/template"
	"net/http"
)

var templates = template.Must(template.ParseGlob("templates/*.html"))

func init() {
	routes := map[string]http.HandlerFunc{
		// Test run results, viewed by browser (default view)
		// For run results diff view, 'before' and 'after' params can be given.
		"/": testHandler,

		// About wpt.fyi
		"/about": aboutHandler,

		// Test run results, viewed by pass-rate across the browsers
		"/interop/": interopHandler,

		// Lists of test run results which have poor interoperability
		"/interop/anomalies": anomalyHandler,

		// List of all test runs, by SHA[0:10]
		"/test-runs": testRunsHandler,

		// API endpoint for diff of two test run summary JSON blobs.
		"/api/diff": apiDiffHandler,

		// API endpoint for listing all test runs for a given SHA.
		"/api/runs": apiTestRunsHandler,

		// API endpoint for a single test run.
		"/api/run": apiTestRunHandler,

		// API endpoint for redirecting to a run's summary JSON blob.
		"/results": resultsRedirectHandler,
	}

	for route, handler := range routes {
		http.HandleFunc(route, wrapHSTS(handler))
	}
}

func wrapHSTS(h http.HandlerFunc) http.HandlerFunc {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		value := "max-age=31536000; includeSubDomains; preload"
		w.Header().Add("Strict-Transport-Security", value)
		h(w, r)
	})
}
