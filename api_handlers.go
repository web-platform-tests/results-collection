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
	"io/ioutil"
	"net/http"
	"net/url"
	"time"

	"google.golang.org/appengine"
	"google.golang.org/appengine/datastore"
	"fmt"
)

// apiTestRunsHandler is responsible for emitting test-run JSON for all the runs at a given SHA.
//
// URL Params:
//     sha: SHA[0:10] of the repo when the tests were executed (or 'latest')
func apiTestRunsHandler(w http.ResponseWriter, r *http.Request) {
	runSHA, err := ParseSHAParam(r)
	if err != nil {
		http.Error(w, "Invalid query params", http.StatusBadRequest)
		return
	}

	ctx := appengine.NewContext(r)
	var browserNames []string
	if browserNames, err = GetBrowserNames(); err != nil {
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

func apiTestRunHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		apiTestRunPostHandler(w, r)
	} else if r.Method == "GET" {
		apiTestRunGetHandler(w, r)
	} else {
		http.Error(w, "This endpoint only supports GET and POST.", http.StatusMethodNotAllowed)
	}
}

// apiTestRunGetHandler is responsible for emitting the test-run JSON a specific run,
// identified by a named browser (platform) at a given SHA.
//
// URL Params:
//     sha: SHA[0:10] of the repo when the test was executed (or 'latest')
//     browser: Browser for the run (e.g. 'chrome', 'safari-10')
func apiTestRunGetHandler(w http.ResponseWriter, r *http.Request) {
	runSHA, err := ParseSHAParam(r)
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

// apiTestRunPostHandler is responsible for handling TestRun submissions (via HTTP POST requests).
// It asserts the presence of a required secret token, then saves the JSON blob to the Datastore.
// See models.go for the JSON format expected.
func apiTestRunPostHandler(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)
	var err error

	// Fetch pre-uploaded Token entity.
	suppliedSecret := r.URL.Query().Get("secret")
	tokenKey := datastore.NewKey(ctx, "Token", "upload-token", 0, nil)
	var token Token
	if err = datastore.Get(ctx, tokenKey, &token); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if suppliedSecret != token.Secret {
		http.Error(w, fmt.Sprintf("Invalid token '%s'", suppliedSecret), http.StatusUnauthorized)
		return
	}

	var body []byte
	if body, err = ioutil.ReadAll(r.Body); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	var testRun TestRun
	if err = json.Unmarshal(body, &testRun); err != nil {
		http.Error(w, "Failed to parse JSON: " + err.Error(), http.StatusBadRequest)
		return
	}
	testRun.CreatedAt = time.Now()

	// Create a new TestRun out of the JSON body of the request.
	key := datastore.NewIncompleteKey(ctx, "TestRun", nil)
	if _, err := datastore.Put(ctx, key, &testRun); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	var jsonOutput []byte
	if jsonOutput, err = json.Marshal(testRun); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Write(jsonOutput)
	w.WriteHeader(http.StatusCreated)
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
