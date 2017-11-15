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
	"sort"
	"time"

	"google.golang.org/appengine"
	"google.golang.org/appengine/datastore"
	"net/url"
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

	// Fetch pre-uploaded Token entity.
	var queryParams url.Values
	var err error
	if queryParams, err = url.ParseQuery(r.URL.RawQuery); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	suppliedSecret := queryParams.Get("secret")
	tokenKey := datastore.NewKey(ctx, "Token", "upload-token", 0, nil)
	var token Token
	if err = datastore.Get(ctx, tokenKey, &token); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if suppliedSecret != token.Secret {
		http.Error(w, fmt.Sprintf("Invalid token '%s'", suppliedSecret), http.StatusUnauthorized)
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

	// Create a new TestRun out of the JSON body of the request.
	key := datastore.NewIncompleteKey(ctx, "TestRun", nil)
	if _, err := datastore.Put(ctx, key, &testRun); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	var jsonBytes []byte
	if jsonBytes, err = json.Marshal(testRun); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Write(jsonBytes)
	w.WriteHeader(http.StatusCreated)
}

func handleGet(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)
	var err error
	var browserNames []string
	if browserNames, err = GetBrowserNames(); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	baseQuery := datastore.NewQuery("TestRun").Order("-CreatedAt").Limit(100)

	var runs []TestRun
	for _, browserName := range browserNames {
		var queryResults []TestRun
		query := baseQuery.Filter("BrowserName =", browserName)
		if _, err := query.GetAll(ctx, &queryResults); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		runs = append(runs, queryResults...)
	}
	sort.Sort(byCreatedAtDesc(runs))

	// Serialize the data + pipe through the test-runs.html template.
	testRunsBytes, err := json.Marshal(runs)
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

type byCreatedAtDesc []TestRun

func (a byCreatedAtDesc) Len() int           { return len(a) }
func (a byCreatedAtDesc) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a byCreatedAtDesc) Less(i, j int) bool { return a[i].CreatedAt.Before(a[j].CreatedAt) }
