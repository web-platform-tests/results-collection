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
    "net/http"
    "time"
    "fmt"

    "google.golang.org/appengine"
    "google.golang.org/appengine/datastore"
)

// Create TestRun entities for local development and testing.
// These point to JSON files stored in /static/.
// Key names for each entity are specified to make this route idempotent.
func populateDevData(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)

    devData := map[string]*TestRun{
        "dev-testrun-chrome-63": &TestRun{
            BrowserName: "chrome",
            BrowserVersion: "63.0",
            OSName: "linux",
            OSVersion: "3.16",
            Revision: "b952881825",
            ResultsURL: "/static/b952881825/chrome-63.0-linux-summary.json.gz",
            CreatedAt: time.Now(),
        },
        "dev-testrun-edge-15": &TestRun{
            BrowserName: "edge",
            BrowserVersion: "15",
            OSName: "windows",
            OSVersion: "10",
            Revision: "b952881825",
            ResultsURL: "/static/b952881825/edge-15-windows-10-sauce-summary.json.gz",
            CreatedAt: time.Now(),
        },
        "dev-testrun-firefox-57": &TestRun{
            BrowserName: "firefox",
            BrowserVersion: "57.0",
            OSName: "linux",
            OSVersion: "*",
            Revision: "b952881825",
            ResultsURL: "/static/b952881825/firefox-57.0-linux-summary.json.gz",
            CreatedAt: time.Now(),
        },
        "dev-testrun-safari-10": &TestRun{
            BrowserName: "safari",
            BrowserVersion: "10",
            OSName: "macos",
            OSVersion: "10.12",
            Revision: "b952881825",
            ResultsURL: "/static/b952881825/safari-10-macos-10.12-sauce-summary.json.gz",
            CreatedAt: time.Now(),
        },
    }

    for key, testRun := range devData {
        key := datastore.NewKey(ctx, "TestRun", key, 0, nil)
        if _, err := datastore.Put(ctx, key, testRun); err != nil {
            http.Error(w, err.Error(), http.StatusInternalServerError)
            return
        }
    }

    fmt.Fprintf(w, "Successfully created %d TestRuns.", len(devData))
}
