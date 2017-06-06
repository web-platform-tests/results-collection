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

    "appengine"
    "appengine/datastore"
)

func testHandler(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)

    var testRuns []TestRun
    var chromeTestRuns []TestRun
    var firefoxTestRuns []TestRun
    baseQuery := datastore.NewQuery("TestRun").Order("-CreatedAt").Limit(1)
    chromeQuery := baseQuery.Filter("BrowserName =", "chrome")
    firefoxQuery := baseQuery.Filter("BrowserName =", "firefox")

    if _, err := chromeQuery.GetAll(ctx, &chromeTestRuns); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
    if _, err := firefoxQuery.GetAll(ctx, &firefoxTestRuns); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
    testRuns = append(testRuns, chromeTestRuns...)
    testRuns = append(testRuns, firefoxTestRuns...)

    testRunsBytes, err := json.Marshal(testRuns)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
    testRunsJSON := string(testRunsBytes)


    var templatePath string
    if r.URL.Path == "/" {
        templatePath = "index.html"
    } else {
        templatePath = "test.html"
    }

    if err := templates.ExecuteTemplate(w, templatePath, testRunsJSON); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
}
