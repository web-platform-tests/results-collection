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
    "errors"
    "fmt"
    "net/http"
    "regexp"
    "strings"

    "appengine"
    "appengine/datastore"
)

// This handler is responsible for redirecting to the Google Cloud Storage API
// JSON blob for the latest TestRun for the given browser.
//
// URL format:
// /latest/{browser}[/{test}]
func latestResultsRedirectHandler(w http.ResponseWriter, r *http.Request) {
    remainingPath := strings.Replace(r.URL.Path, "/latest/", "", 1)
    pathPieces := strings.SplitN(remainingPath, "/", 2)
    if len(pathPieces) > 2 {
      http.Error(w, "Invalid path", http.StatusBadRequest)
      return
    }

    latestRun, err := getLatestRun(r, pathPieces[0])
    if err != nil {
      http.Error(w, err.Error(), http.StatusInternalServerError)
      return
    }
    if (TestRun{}) == latestRun {
      http.NotFound(w, r)
      return
    }

    var testFile *string
    if len(pathPieces) > 1 {
      testFile = &pathPieces[1]
    }
    resultsURL := getResultsURL(latestRun, testFile)

    http.Redirect(w, r, resultsURL, http.StatusFound)
}

func getLatestRun(r *http.Request, browser string) (latest TestRun, err error) {
    browserPieces := strings.Split(browser, "-")
    if len(browserPieces) < 1 || len(browserPieces) > 4 {
      err = errors.New("Invalid path")
      return
    }

    ctx := appengine.NewContext(r)
    baseQuery := datastore.NewQuery("TestRun").Order("-CreatedAt").Limit(1)

    var testRunResults []TestRun
    query := baseQuery.Filter("BrowserName =", browserPieces[0])
    if len(browserPieces) > 1 {
      query = query.Filter("BrowserVersion =", browserPieces[1])
    }
    if len(browserPieces) > 2 {
      query = query.Filter("OSName =", browserPieces[2])
    }
    if len(browserPieces) > 3 {
      query = query.Filter("OSVersion =", browserPieces[3])
    }
    _, err = query.GetAll(ctx, &testRunResults)
    if err != nil {
        return
    }
    if len(testRunResults) > 0 {
      latest = testRunResults[0]
    }
    return
}

func getResultsURL(latestRun TestRun, testFile *string) (resultsURL string) {
    resultsURL = latestRun.ResultsURL
    if testFile != nil {
        // Assumes that result files are under a directory named SHA[0:10].
        resultsBase := strings.SplitAfter(resultsURL, "/" + latestRun.Revision)[0];
        resultsPieces := strings.Split(resultsURL, "/")
        re := regexp.MustCompile("(-summary)?\\.json\\.gz$")
        platform := re.ReplaceAllString(resultsPieces[len(resultsPieces) - 1], "")
        resultsURL = fmt.Sprintf("%s/%s/%s", resultsBase, platform, *testFile)
    }
    return resultsURL
}
