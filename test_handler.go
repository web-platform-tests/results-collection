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
    "context"
    "encoding/json"
    "net/http"
    "net/url"
    "io/ioutil"
    "regexp"
    "sort"

    "google.golang.org/appengine"
    "google.golang.org/appengine/datastore"
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

    ctx := appengine.NewContext(r)
    var bytes []byte
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

    // Make sure to show results for the same complete run (executed for all browsers).
    if runSHA == "latest" {
        runSHA, err = getLastCompleteRunSHA(ctx, browserNames)
        if err != nil {
            http.Error(w, err.Error(), http.StatusInternalServerError)
            return
        }
    }

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

    data := struct {
        TestRuns string
        SHA      string
    }{
        string(testRunsBytes),
        runSHA,
    }

    if err := templates.ExecuteTemplate(w, "index.html", data); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
}

// ParseSHAParam parses and validates the 'sha' param for the request.
// It returns "latest" by default (and in error cases).
func ParseSHAParam(r *http.Request) (runSHA string, err error) {
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

// getLastCompleteRunSHA returns the SHA[0:10] for the most recent run that complete for all of the given browser names.
func getLastCompleteRunSHA(ctx context.Context, browserNames []string) (sha string, err error) {
    baseQuery := datastore.
        NewQuery("TestRun").
        Order("-CreatedAt").
        Limit(100).
        Project("Revision")

    runSHAs := make(map[string]int)
    for _, browser := range browserNames {
        it := baseQuery.Filter("BrowserName = ", browser).Run(ctx)
        for {
            var testRun TestRun
            _, err := it.Next(&testRun)
            if err == datastore.Done {
                break
            }
            if err != nil {
                return "latest", err
            }
            if _, ok := runSHAs[testRun.Revision]; !ok {
                runSHAs[testRun.Revision] = 1
            } else {
                sum := runSHAs[testRun.Revision] + 1
                if sum == len(browserNames) {
                    return testRun.Revision, nil
                }
                runSHAs[testRun.Revision] = sum
            }
        }
    }
    return "latest", nil
}