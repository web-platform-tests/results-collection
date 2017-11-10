// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package wptdashboard

import (
	"encoding/json"
	"net/http"
	"net/url"

	"google.golang.org/appengine"
	"google.golang.org/appengine/datastore"
)

// apiTestRunsHandler is responsible for emitting test-run JSON for all the runs at a given SHA.
//
// URL Params:
//     sha: SHA[0:10] of the repo when the tests were executed (or 'latest')
func apiTestRunsHandler(w http.ResponseWriter, r *http.Request) {
	runSHA, err := GetRunSHA(r)
	if err != nil {
		http.Error(w, "Invalid query params", http.StatusBadRequest)
		return
	}

	ctx := appengine.NewContext(r)
	var browserNames []string
	browserNames, err = GetBrowserNames()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	var testRuns []TestRun
	baseQuery := datastore.NewQuery("TestRun").Order("-CreatedAt").Limit(1)

	for _, browserName := range browserNames {
		var testRunResults []TestRun
		query := baseQuery.Filter("BrowserName =", browserName)
		if runSHA != "" && runSHA != "latest" {
			query = query.Filter("Revision =", runSHA)
		}
		if _, err := query.GetAll(ctx, &testRunResults); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		testRuns = append(testRuns, testRunResults...)
	}

	testRunsBytes, err := json.Marshal(testRuns)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Write(testRunsBytes)
}

// apiTestRunHandler is responsible for emitting the test-run JSON a specific run,
// identified by a named browser (platform) at a given SHA.
//
// URL Params:
//     sha: SHA[0:10] of the repo when the test was executed (or 'latest')
//     browser: Browser for the run (e.g. 'chrome', 'safari-10')
func apiTestRunHandler(w http.ResponseWriter, r *http.Request) {
	runSHA, err := GetRunSHA(r)
	if err != nil {
		http.Error(w, "Invalid query params", http.StatusBadRequest)
		return
	}

	var browserName string
	browserName, err = getBrowserParam(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	} else if browserName == "" {
		http.Error(w, "Invalid 'browser' param", http.StatusBadRequest)
		return
	}

	ctx := appengine.NewContext(r)

	query := datastore.
		NewQuery("TestRun").
		Order("-CreatedAt").
		Limit(1).
		Filter("BrowserName =", browserName)
	if runSHA != "" && runSHA != "latest" {
		query = query.Filter("Revision =", runSHA)
	}

	var testRuns []TestRun
	if _, err := query.GetAll(ctx, &testRuns); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if len(testRuns) == 0 {
		http.NotFound(w, r)
		return
	}

	testRunsBytes, err := json.Marshal(testRuns[0])
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Write(testRunsBytes)
}

// getBrowserParam parses and validates the 'browser' param for the request.
// It returns "" by default (and in error cases).
func getBrowserParam(r *http.Request) (browser string, err error) {
	browser = ""
	params, err := url.ParseQuery(r.URL.RawQuery)
	if err != nil {
		return browser, err
	}

	browserNames, err := GetBrowserNames()
	if err != nil {
		return browser, err
	}

	browser = params.Get("browser")
	// Check that it's a browser name we recognize.
	for _, name := range browserNames {
		if name == browser {
			return name, nil
		}
	}
	return "", nil
}
