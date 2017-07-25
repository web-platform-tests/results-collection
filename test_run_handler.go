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
    "fmt"
    "time"
    "appengine"
    "appengine/datastore"
)

func testRunHandler(w http.ResponseWriter, r *http.Request) {
    var err error
    ctx := appengine.NewContext(r)

    if r.Method != "POST" {
        http.Error(w, "This endpoint only supports POST.", http.StatusMethodNotAllowed)
        return
    }

    var body []byte
    if body, err = ioutil.ReadAll(r.Body); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    var testRun TestRun
    if err = json.Unmarshal(body, &testRun); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    testRun.CreatedAt = time.Now()

    fmt.Fprintf(w, "got... %v", testRun)

    key := datastore.NewIncompleteKey(ctx, "TestRun", nil)
    if _, err := datastore.Put(ctx, key, &testRun); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    fmt.Fprintf(w, "Successfully... %v", testRun)
}
