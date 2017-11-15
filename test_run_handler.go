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

	"google.golang.org/appengine"
	"google.golang.org/appengine/datastore"
)

// testRunsHandler handles GET/POST requests to /test-runs
func testRunsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		// /test-runs is the legacy POST endpoint, migrated to /api/runs and left to avoid breakages.
		apiTestRunPostHandler(w, r)
	} else if r.Method == "GET" {
		handleTestRunGet(w, r)
	} else {
		http.Error(w, "This endpoint only supports GET and POST.", http.StatusMethodNotAllowed)
	}
}

func handleTestRunGet(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)
	var err error
	var browserNames []string
	if browserNames, err = GetBrowserNames(); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	baseQuery := datastore.NewQuery("TestRun").Order("-CreatedAt").Limit(100)
	runs := make(map[string][]TestRun)
	for _, browserName := range browserNames {
		var testRunResults []TestRun
		query := baseQuery.Filter("BrowserName =", browserName)
		if _, err := query.GetAll(ctx, &testRunResults); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		for _, r := range testRunResults {
			if _, ok := runs[r.Revision]; !ok {
				runs[r.Revision] = make([]TestRun, 0)
			}
			runs[r.Revision] = append(runs[r.Revision], r)
		}
	}

	// Serialize the data + pipe through the test-runs.html template.
	testRunsBytes, err := json.Marshal(runs)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	data := struct {
		TestRuns string
	}{
		string(testRunsBytes),
	}

	if err := templates.ExecuteTemplate(w, "test-runs.html", data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}
