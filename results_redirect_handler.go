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
	"net/url"
	"regexp"
	"strings"

	"google.golang.org/appengine"
	"google.golang.org/appengine/datastore"
)

// resultsRedirectHandler is responsible for redirecting to the Google Cloud Storage API
// JSON blob for the given SHA (or latest) TestRun for the given browser.
//
// URL format:
// /results
//
// Params:
//   platform: Browser (and OS) of the run, e.g. "chrome-63.0" or "safari"
//   (optional) run: SHA[0:10] of the test run, or "latest" (latest is the default)
//   (optional) test: Path of the test, e.g. "/css/css-images-3/gradient-button.html"
func resultsRedirectHandler(w http.ResponseWriter, r *http.Request) {
	params, err := url.ParseQuery(r.URL.RawQuery)
	if err != nil {
		http.Error(w, "Invalid path", http.StatusBadRequest)
		return
	}

	platform := params.Get("platform")
	if platform == "" {
		http.Error(w, "Param 'platform' missing", http.StatusBadRequest)
		return
	}

	runSHA := params.Get("sha")
	if runSHA == "" {
		// Legacy name, in case still present in scripts/local stores.
		runSHA = params.Get("run")
	}
	if runSHA == "" {
		runSHA = "latest"
	}

	run, err := getRun(r, runSHA, platform)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if (TestRun{}) == run {
		http.Error(w, fmt.Sprintf("404 - Test run '%s' not found", runSHA), http.StatusNotFound)
		return
	}

	test := params.Get("test")
	resultsURL := getResultsURL(run, test)

	http.Redirect(w, r, resultsURL, http.StatusFound)
}

func getRun(r *http.Request, run string, platform string) (latest TestRun, err error) {
	platformPieces := strings.Split(platform, "-")
	if len(platformPieces) < 1 || len(platformPieces) > 4 {
		err = errors.New("Invalid path")
		return
	}

	ctx := appengine.NewContext(r)
	baseQuery := datastore.NewQuery("TestRun").Order("-CreatedAt").Limit(1)

	var testRunResults []TestRun
	query := baseQuery.Filter("BrowserName =", platformPieces[0])
	if run != "" && run != "latest" {
		query = query.Filter("Revision =", run)
	}
	if len(platformPieces) > 1 {
		query = query.Filter("BrowserVersion =", platformPieces[1])
	}
	if len(platformPieces) > 2 {
		query = query.Filter("OSName =", platformPieces[2])
	}
	if len(platformPieces) > 3 {
		query = query.Filter("OSVersion =", platformPieces[3])
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

func getResultsURL(run TestRun, testFile string) (resultsURL string) {
	resultsURL = run.ResultsURL
	if testFile != "" && testFile != "/" {
		// Assumes that result files are under a directory named SHA[0:10].
		resultsBase := strings.SplitAfter(resultsURL, "/"+run.Revision)[0]
		resultsPieces := strings.Split(resultsURL, "/")
		re := regexp.MustCompile("(-summary)?\\.json\\.gz$")
		platform := re.ReplaceAllString(resultsPieces[len(resultsPieces)-1], "")
		resultsURL = fmt.Sprintf("%s/%s/%s", resultsBase, platform, testFile)
	}
	return resultsURL
}
