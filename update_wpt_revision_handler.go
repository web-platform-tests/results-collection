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
    "io/ioutil"
    "net/http"
    "time"

    "appengine"
    "appengine/datastore"
    "appengine/urlfetch"
)

func updateWPTRevisionHandler(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)
    w.Header().Set("Content-Type", "text/plain; charset=utf-8")

    gitHubWPTSHA, _ := fetchLatestWPTRevisionFromGitHubAPI(ctx)

    var results []WPTRevision
    q := datastore.NewQuery("WPTRevision").Order("-Number").Limit(1)
    if _, err := q.GetAll(ctx, &results); err != nil {
        fmt.Fprintf(w, "Error fetching current WPTD revision: %s\n", err)
        return
    }
    fmt.Fprintf(w, "GH SHA: %s\n", gitHubWPTSHA)
    newNumber := 0

    if len(results) > 0 {
        fmt.Fprintf(w, "WPTD SHA: %s\n", results[0].SHA)

        if gitHubWPTSHA == results[0].SHA {
            fmt.Fprintf(w, "SHAs match, stopping.\n")
            return
        }

        newNumber = results[0].Number + 1
    } else {
        fmt.Fprintf(w, "No current revision, creating first WPTRevision.\n")
    }

    fmt.Fprintf(w, "Creating new revision.\n")

    newRevision := &WPTRevision{
        SHA:    gitHubWPTSHA,
        Number: newNumber,
        Retain: true,
        CreatedAt: time.Now(),
    }
    key := datastore.NewKey(ctx, "WPTRevision", gitHubWPTSHA, 0, nil)

    if _, err := datastore.Put(ctx, key, newRevision); err != nil {
        http.Error(w, err.Error(), 500)
        return
    }

    fmt.Fprintf(w, "Created: %+v\n", newRevision)
}

func getLatestWPTRevision(ctx appengine.Context) ([]WPTRevision, error) {
    var wptRevision []WPTRevision
    q := datastore.NewQuery("WPTRevision").Limit(1)
    _, err := q.GetAll(ctx, &wptRevision)
    return wptRevision, err
}

func fetchLatestWPTRevisionFromGitHubAPI(ctx appengine.Context) (string, error) {
    client := urlfetch.Client(ctx)
    resp, err := client.Get("https://api.github.com/repos/w3c/web-platform-tests/commits/master")
    if err != nil {
            return "", err
    }

    defer resp.Body.Close()
    body, err := ioutil.ReadAll(resp.Body)

    var commit struct {
        SHA string `json:"sha"`
    }
    // TODO: can we pass json.Unmarshal a raw file handle?
    err = json.Unmarshal(body, &commit)
    if err != nil {
        fmt.Println("error:", err)
    }

    return commit.SHA, nil
}
