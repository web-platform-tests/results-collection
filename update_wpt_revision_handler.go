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
    "encoding/json"
    "io/ioutil"

    "appengine"
    "appengine/datastore"
    "appengine/urlfetch"
    "fmt"
)

func updateWPTRevisionHandler(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)
    gitHubWPTRevisionSHA, _ := fetchLatestWPTRevisionFromGitHubAPI(ctx)
    fmt.Fprintf(w, "sha: %s", gitHubWPTRevisionSHA)


    // - fetch latest WPTRevision in datastore
    // - if API revision == latest revision, quit
    latestRevs, err := getLatestWPTRevision(ctx)
    if err != nil {
        fmt.Fprintf(w, "yes %s", err)
        return
    }
    var newRev *WPTRevision
    if len(latestRevs) == 0 {
        fmt.Fprintf(w, "create new")
        newRev = &WPTRevision{1, true}
    } else {
        fmt.Fprintf(w, "overwrite")
        latestRev := latestRevs[0]
        newRev = &WPTRevision{latestRev.Number + 1, false}
    }
    key := datastore.NewKey(ctx, "WPTRevision", gitHubWPTRevisionSHA, 0, nil)

    if _, err := datastore.Put(ctx, key, newRev); err != nil {
        http.Error(w, err.Error(), 500)
        return
    }

    // - else, create new WPTRevision
}

// func getLatestWPTRevision(ctx context.Context) {
//}


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
