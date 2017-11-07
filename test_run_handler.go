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

    "google.golang.org/appengine"
    "google.golang.org/appengine/datastore"
    "sort"
    "context"
    "bytes"
)

func testRunHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method == "POST" {
        handlePost(w, r)
    } else if r.Method == "GET" {
        handleGet(w, r)
    } else {
        http.Error(w, "This endpoint only supports GET and POST.", http.StatusMethodNotAllowed)
    }
}

func handlePost(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)
    var err error

    // Fetch pre-uploaded Token entity.
    suppliedSecret := r.URL.Query().Get("secret")
    tokenKey := datastore.NewKey(ctx, "Token", "upload-token", 0, nil)
    var token Token
    if err = datastore.Get(ctx, tokenKey, &token); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    if suppliedSecret != token.Secret {
        http.Error(w, err.Error(), http.StatusUnauthorized)
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

    // Create a new TestRun out of the JSON body of the request.
    key := datastore.NewIncompleteKey(ctx, "TestRun", nil)
    if _, err := datastore.Put(ctx, key, &testRun); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    fmt.Fprintf(w, "Successfully created TestRun... %v", testRun)
    w.WriteHeader(http.StatusCreated)
}

func handleGet(w http.ResponseWriter, r *http.Request) {
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

    baseQuery := datastore.
        NewQuery("TestRun").
        Order("-CreatedAt").
        Limit(100)

    var browserNames []string
    for _, browser := range browsers {
        if browser.InitiallyLoaded {
            browserNames = append(browserNames, browser.BrowserName)
        }
    }
    sort.Strings(browserNames)

    runs := make(map[string][]TestRun)
    createdAtLimit := time.Now()
    for _, browserName := range browserNames {
        var testRunResults []TestRun
        query := baseQuery.Filter("BrowserName =", browserName)
        if _, err := query.GetAll(ctx, &testRunResults); err != nil {
            http.Error(w, err.Error(), http.StatusInternalServerError)
            return
        }
        for _, r := range testRunResults {
            if _, ok := runs[r.Revision]; !ok {
                runs[r.Revision] = make([]TestRun, 0)
            }
            runs[r.Revision] = append(runs[r.Revision], r)
            if r.CreatedAt.Before(createdAtLimit) {
                createdAtLimit = r.CreatedAt
            }
        }
    }

    var orderedSHAs []string
    orderedSHAs, err = getOrderedSHAs(ctx, createdAtLimit)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    // Serialize the data + pipe through the test-runs.html template.
    testRunsBytes, err := marshalInOrder(runs, orderedSHAs)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    data := struct {
        TestRuns string
    }{
        string(testRunsBytes),
    }

    if err := templates.ExecuteTemplate(w, "test-runs.html", data); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
}

// getOrderedSHAs loads SHAs in descending chronological order. This allows us to preserve the ordering of the SHAs,
// in spite of appending runs by loading each browsers runs separately.
func getOrderedSHAs(ctx context.Context, createdAtLimit time.Time) (shas []string, err error) {
    it := datastore.
        NewQuery("TestRun").
        Project("CreatedAt", "Revision").Distinct().
        Filter("CreatedAt >= ", createdAtLimit).
        Order("-CreatedAt").
        Run(ctx)
    shas = make([]string, 0)
    last := ""
    for {
        var testRun TestRun
        _, err := it.Next(&testRun)
        if err == datastore.Done {
            break
        }
        if err != nil {
            return nil, err
        }
        if last == testRun.Revision {
            continue
        }
        shas = append(shas, testRun.Revision)
    }
    return shas, nil
}

// marshalInOrder produces a marshaled JSON map for the given map which follows
// the ordering of the given keys array. By default, json.Marshal sorts the keys.
func marshalInOrder(runs map[string][]TestRun, keys []string) ([]byte, error) {
    var output bytes.Buffer
    output.WriteByte('{')
    first := true
    for _, key := range keys {
        if _, ok := runs[key]; !ok {
            continue
        }
        if !first {
            output.WriteByte(',')
        } else {
            first = false
        }
        // Key
        serialized, err := json.Marshal(key)
        if err != nil {
            return nil, err
        }
        output.Write(serialized)
        output.WriteByte(':')
        // Value
        serialized, err = json.Marshal(runs[key])
        if err != nil {
            return nil, err
        }
        output.Write(serialized)
    }
    output.WriteByte('}')
    return output.Bytes(), nil
}