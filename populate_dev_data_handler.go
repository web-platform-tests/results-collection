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

func populateDevData(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)

    // Add Chrome TestRun
    testRun := &TestRun{
        Revision: "e2d2cde03d",
        BrowserName: "chrome",
        BrowserVersion: "60.0",
        OSName: "debian",
        OSVersion: "8",
        ResultsURL: "/static/chrome-60.0-debian-8.json",
        CreatedAt: time.Now(),
    }

    // Specify key to make this route idempotent
    key := datastore.NewKey(ctx, "TestRun", "dev-testrun-chrome-60", 0, nil)
    if _, err := datastore.Put(ctx, key, testRun); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }

    // Add Firefox TestRun
    testRun = &TestRun{
        Revision: "e2d2cde03d",
        BrowserName: "firefox",
        BrowserVersion: "55.0",
        OSName: "debian",
        OSVersion: "8",
        ResultsURL: "/static/firefox-55.0-debian-8.json",
        CreatedAt: time.Now(),
    }

    // Specify key to make this route idempotent
    key = datastore.NewKey(ctx, "TestRun", "dev-testrun-firefox-55", 0, nil)
    if _, err := datastore.Put(ctx, key, testRun); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }

    fmt.Fprintf(w, "Successfully created 2 TestRuns.")
}
