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
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"

	"golang.org/x/net/context"
	"google.golang.org/appengine/datastore"
	"google.golang.org/appengine/urlfetch"
)

type platformAtRevision struct {
	// Platform is the string representing browser (+ version), and OS (+ version).
	Platform string

	// Revision is the SHA[0:10] of the git repo.
	Revision string
}

func parsePlatformAtRevisionSpec(spec string) (platformAtRevision platformAtRevision, err error) {
	pieces := strings.Split(spec, "@")
	if len(pieces) > 2 {
		return platformAtRevision, errors.New("invalid platform@revision spec: " + spec)
	}
	platformAtRevision.Platform = pieces[0]
	if len(pieces) < 2 {
		// No @ is assumed to be the platform only.
		platformAtRevision.Revision = "latest"
	} else {
		platformAtRevision.Revision = pieces[1]
	}
	// TODO(lukebjerring): Also handle actual platforms (with version + os)
	if IsBrowserName(platformAtRevision.Platform) {
		return platformAtRevision, nil
	}
	return platformAtRevision, errors.New("Platform " + platformAtRevision.Platform + " not found")
}

func fetchRunResultsJSONForParam(
	ctx context.Context, r *http.Request, revision string) (results map[string][]int, err error) {
	var spec platformAtRevision
	if spec, err = parsePlatformAtRevisionSpec(revision); err != nil {
		return nil, err
	}
	return fetchRunResultsJSONForSpec(ctx, r, spec)
}

func fetchRunResultsJSONForSpec(
	ctx context.Context, r *http.Request, revision platformAtRevision) (results map[string][]int, err error) {
	var run TestRun
	if run, err = fetchRunForSpec(ctx, revision); err != nil {
		return nil, err
	} else if (run == TestRun{}) {
		return nil, nil
	}
	return fetchRunResultsJSON(ctx, r, run)
}

func fetchRunForSpec(ctx context.Context, revision platformAtRevision) (TestRun, error) {
	baseQuery := datastore.
		NewQuery("TestRun").
		Order("-CreatedAt").
		Limit(1)

	var results []TestRun
	// TODO(lukebjerring): Handle actual platforms (split out version + os)
	query := baseQuery.
		Filter("BrowserName =", revision.Platform)
	if revision.Revision != "latest" {
		query = query.Filter("Revision = ", revision.Revision)
	}
	if _, err := query.GetAll(ctx, &results); err != nil {
		return TestRun{}, err
	}
	if len(results) < 1 {
		return TestRun{}, nil
	}
	return results[0], nil
}

// fetchRunResultsJSON fetches the results JSON summary for the given test run, but does not include subtests (since
// a full run can span 20k files).
func fetchRunResultsJSON(ctx context.Context, r *http.Request, run TestRun) (results map[string][]int, err error) {
	client := urlfetch.Client(ctx)
	url := run.ResultsURL
	if strings.Index(url, "/") == 0 {
		reqURL := *r.URL
		reqURL.Path = url
	}
	var resp *http.Response
	if resp, err = client.Get(url); err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("%s returned HTTP status %d", url, resp.StatusCode)
	}
	var body []byte
	if body, err = ioutil.ReadAll(resp.Body); err != nil {
		return nil, err
	}
	if err = json.Unmarshal(body, &results); err != nil {
		return nil, err
	}
	return results, nil
}

// getResultsDiff returns a map of test name to an array of [count-different-tests, total-tests], for tests which had
// different results counts in their map (which is test name to array of [count-passed, total-tests]).
//
func getResultsDiff(before map[string][]int, after map[string][]int, filter DiffFilterParam) map[string][]int {
	diff := make(map[string][]int)
	if filter.Deleted || filter.Changed {
		for test, resultsBefore := range before {
			if resultsAfter, ok := after[test]; !ok {
				// Missing? Then N / N tests are 'different'.
				if !filter.Deleted {
					continue
				}
				diff[test] = []int{resultsBefore[1], resultsBefore[1]}
			} else {
				if !filter.Changed {
					continue
				}
				passDiff := abs(resultsBefore[0] - resultsAfter[0])
				countDiff := abs(resultsBefore[1] - resultsAfter[1])
				if countDiff == 0 && passDiff == 0 {
					continue
				}
				// Changed tests is at most the number of different outcomes,
				// but newly introduced tests should still be counted (e.g. 0/2 => 0/5)
				diff[test] = []int{
					max(passDiff, countDiff),
					max(resultsBefore[1], resultsAfter[1]),
				}
			}
		}
	}
	if filter.Added {
		for test, resultsAfter := range after {
			if _, ok := before[test]; !ok {
				// Missing? Then N / N tests are 'different'
				diff[test] = []int{resultsAfter[1], resultsAfter[1]}
			}
		}
	}
	return diff
}
