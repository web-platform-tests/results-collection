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
	Platform string
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
	query := baseQuery.
		Filter("BrowserName =", revision.Platform)
	if revision.Revision != "latest" {
		query.Filter("Revision = ", revision.Revision)
	}
	if _, err := query.GetAll(ctx, &results); err != nil {
		return TestRun{}, err
	}
	if len(results) < 1 {
		return TestRun{}, nil
	}
	return results[0], nil
}

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

func diffResults(before map[string][]int, after map[string][]int) map[string][]int {
	diff := make(map[string][]int)
	for test, resultsBefore := range before {
		if resultsAfter, ok := after[test]; !ok {
			// Missing? Then N / N tests are 'different'
			diff[test] = []int{resultsBefore[1], resultsBefore[1]}
		} else {
			passDiff := abs(resultsBefore[0] - resultsAfter[0])
			countDiff := abs(resultsBefore[1] - resultsAfter[1])
			if countDiff == 0 && passDiff == 0 {
				continue
			}
			diff[test] = []int{passDiff + countDiff, max(resultsBefore[1], resultsAfter[1])}
		}
	}
	for test, resultsAfter := range after {
		if _, ok := before[test]; !ok {
			// Missing? Then N / N tests are 'different'
			diff[test] = []int{resultsAfter[1], resultsAfter[1]}
		}
	}
	return diff
}
