// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package webapp

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
		filter := "ACDU" // Added, Changed, Deleted, Unchanged
		const diffRunURL = `/api/diff?before=%s&after=%s&filter=%s`
		diffRun := models.TestRun{
			Revision:    "diff",
			BrowserName: "diff",
			ResultsURL:  fmt.Sprintf(diffRunURL, specBefore, specAfter, filter),
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
