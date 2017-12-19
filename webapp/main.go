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
	http.HandleFunc("/test-runs", testRunsHandler)
	http.HandleFunc("/about", aboutHandler)
	http.HandleFunc("/api/diff", apiDiffHandler)
	http.HandleFunc("/api/runs", apiTestRunsHandler)
	http.HandleFunc("/api/run", apiTestRunHandler)
	http.HandleFunc("/results", resultsRedirectHandler)
	http.HandleFunc("/", testHandler)
}
