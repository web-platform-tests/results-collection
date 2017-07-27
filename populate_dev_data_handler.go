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

    "appengine"
    "appengine/datastore"
)

// Create TestRun entities for local development and testing.
// These point to JSON files stored in /static/.
// Key names for each entity are specified to make this route idempotent.
func populateDevData(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)

    devData := map[string]*TestRun{
        "dev-testrun-chrome-60": &TestRun{
            Revision: "e2d2cde03d",
            BrowserName: "chrome",
            BrowserVersion: "60.0",
            OSName: "debian",
            OSVersion: "8",
            ResultsURL: "/static/chrome-60.0-debian-8.json",
            CreatedAt: time.Now(),
        },
        "dev-testrun-firefox-55": &TestRun{
            Revision: "e2d2cde03d",
            BrowserName: "firefox",
            BrowserVersion: "55.0",
            OSName: "debian",
            OSVersion: "8",
            ResultsURL: "/static/firefox-55.0-debian-8.json",
            CreatedAt: time.Now(),
        },
        "dev-testrun-edge-15": &TestRun{
            Revision: "dd44fd07c5",
            BrowserName: "edge",
            BrowserVersion: "15",
            OSName: "windows",
            OSVersion: "10",
            ResultsURL: "/static/edge-15-windows-10.json",
            CreatedAt: time.Now(),
        },
        "dev-testrun-safari-10": &TestRun{
            Revision: "dd44fd07c5",
            BrowserName: "safari",
            BrowserVersion: "10",
            OSName: "macos",
            OSVersion: "10.12",
            ResultsURL: "/static/safari-10-macos-10.12.json",
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
