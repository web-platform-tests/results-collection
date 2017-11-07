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
    "fmt"
    "net/http"
    "net/url"
    "io/ioutil"
    "regexp"
    "sort"
)

// This handler is responsible for all pages that display test results.
// It fetches the latest TestRun for each browser then renders the HTML
// page with the TestRuns encoded as JSON. The Polymer app picks those up
// and loads the summary files based on each entity's TestRun.ResultsURL.
//
// The browsers initially displayed to the user are defined in browsers.json.
// The JSON property "initially_loaded" is what controls this.
func testHandler(w http.ResponseWriter, r *http.Request) {
    runSHA, err := GetRunSHA(r)
    if err != nil {
        http.Error(w, "Invalid query params", http.StatusBadRequest)
        return
    }

    var testRunSpecs []string
    var browserNames []string
    browserNames, err = GetBrowserNames()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    for _, browserName := range browserNames {
        testRunSpecs = append(testRunSpecs, fmt.Sprintf("%s@%s", browserName, runSHA))
    }

    testRunSpecsBytes, err := json.Marshal(testRunSpecs)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    data := struct {
        TestRunSpecs string
        SHA      string
    }{
        string(testRunSpecsBytes),
        runSHA,
    }

    if err := templates.ExecuteTemplate(w, "index.html", data); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
}

// GetRunSHA parses and validates the 'sha' param for the request.
// It returns "latest" by default (and in error cases).
func GetRunSHA(r *http.Request) (runSHA string, err error) {
    // Get the SHA for the run being loaded (the first part of the path.)
    runSHA = "latest"
    params, err := url.ParseQuery(r.URL.RawQuery)
    if err != nil {
        return runSHA, err
    }

    runParam := params.Get("sha")
    regex := regexp.MustCompile("[0-9a-fA-F]{10}")
    if regex.MatchString(runParam) {
        runSHA = runParam
    }
    return runSHA, err
}

// GetBrowserNames loads, parses and returns the set of names of browsers
// which are to be included (flagged as initially_loaded in the JSON).
func GetBrowserNames() (browserNames []string, err error) {
    var bytes []byte
    if bytes, err = ioutil.ReadFile("browsers.json"); err != nil {
        return nil, err
    }

    var browsers map[string]Browser
    if err = json.Unmarshal(bytes, &browsers); err != nil {
        return nil, err
    }

    for _, browser := range browsers {
        if browser.InitiallyLoaded {
            browserNames = append(browserNames, browser.BrowserName)
        }
    }
    sort.Strings(browserNames)
    return browserNames, nil
}