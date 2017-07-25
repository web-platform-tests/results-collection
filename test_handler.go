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
    "io/ioutil"
    "sort"

    "appengine"
    "appengine/datastore"
)

// This handler is responsible for all pages that display test results.
// It fetches the latest TestRun for each browser then renders the HTML
// page with the TestRuns encoded as JSON. The Polymer app picks those up
// and loads the summary files based on each entity's TestRun.ResultsURL.
//
// The browsers initially displayed to the user are defined in browsers.json.
// The JSON property "initially_loaded" is what controls this.
func testHandler(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)
    var bytes []byte
    var err error
    var browsers map[string]Browser

    if bytes, err = ioutil.ReadFile("browsers.json"); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    if err = json.Unmarshal(bytes, &browsers); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    var testRuns []TestRun
    baseQuery := datastore.NewQuery("TestRun").Order("-CreatedAt").Limit(1)
    var browserNames []string

    for _, browser := range browsers {
        if browser.InitiallyLoaded {
            browserNames = append(browserNames, browser.BrowserName)
        }
    }
    sort.Strings(browserNames)

    for _, browserName := range browserNames {
        var testRunResults []TestRun
        query := baseQuery.Filter("BrowserName =", browserName)
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
    testRunsJSON := string(testRunsBytes)

    if err := templates.ExecuteTemplate(w, "index.html", testRunsJSON); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
}
