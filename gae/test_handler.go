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

package gae

import (
	"encoding/json"
	"fmt"
	"net/http"

	models "github.com/w3c/wptdashboard/shared"
)

// This handler is responsible for all pages that display test results.
// It fetches the latest TestRun for each browser then renders the HTML
// page with the TestRuns encoded as JSON. The Polymer app picks those up
// and loads the summary files based on each entity's TestRun.ResultsURL.
//
// The browsers initially displayed to the user are defined in browsers.json.
// The JSON property "initially_loaded" is what controls this.
func testHandler(w http.ResponseWriter, r *http.Request) {
	runSHA, err := ParseSHAParam(r)
	if err != nil {
		http.Error(w, "Invalid query params", http.StatusBadRequest)
		return
	}

	var testRunSources []string

	specBefore := r.URL.Query().Get("before")
	specAfter := r.URL.Query().Get("after")
	if specBefore != "" || specAfter != "" {
		if specBefore == "" {
			http.Error(w, "after param provided, but before param missing", http.StatusBadRequest)
			return
		} else if specAfter == "" {
			http.Error(w, "before param provided, but after param missing", http.StatusBadRequest)
			return
		}
		var before platformAtRevision
		var after platformAtRevision
		if before, err = parsePlatformAtRevisionSpec(specBefore); err != nil {
			http.Error(w, "invalid before param", http.StatusBadRequest)
			return
		} else if after, err = parsePlatformAtRevisionSpec(specAfter); err != nil {
			http.Error(w, "invalid after param", http.StatusBadRequest)
			return
		}
		const singleRunURL = `/api/run?sha=%s&browser=%s`
		testRunSources = []string{
			fmt.Sprintf(singleRunURL, before.Revision, before.Platform),
			fmt.Sprintf(singleRunURL, after.Revision, after.Platform),
		}
	} else {
		const sourceURL = `/api/runs?sha=%s`
		testRunSources = []string{fmt.Sprintf(sourceURL, runSHA)}
	}

	testRunSourcesBytes, err := json.Marshal(testRunSources)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	data := struct {
		TestRuns       string
		TestRunSources string
		SHA            string
	}{
		TestRunSources: string(testRunSourcesBytes),
		SHA:            runSHA,
	}

	if specBefore != "" || specAfter != "" {
		const diffRunURL = `/api/diff?before=%s&after=%s`
		diffRun := models.TestRun{
			Revision:    "diff",
			BrowserName: "Diff",
			ResultsURL:  fmt.Sprintf(diffRunURL, specBefore, specAfter),
		}
		var marshaled []byte
		if marshaled, err = json.Marshal([]models.TestRun{diffRun}); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		data.TestRuns = string(marshaled)
	}

	if err := templates.ExecuteTemplate(w, "index.html", data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}
