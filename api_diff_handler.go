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
    "context"
    "encoding/json"
    "errors"
    "io/ioutil"
    "net/http"
    "net/url"
    "strings"

    "google.golang.org/appengine"
    "google.golang.org/appengine/datastore"
    "google.golang.org/appengine/urlfetch"
)

// apiResultsDiffHandler takes 2 test-run results JSON files and produces
// JSON in the same format, with only the differences in runs.
func apiResultsDiffHandler(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)

    var err error
    params, err := url.ParseQuery(r.URL.RawQuery)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
    }

    specBefore := params.Get("before")
    var beforeJSON map[string][]int
    if beforeJSON, err = fetchRunResultsJSONForParam(r, ctx, specBefore); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    } else if beforeJSON == nil {
        http.Error(w, specBefore + " not found", http.StatusNotFound)
        return
    }

    specAfter := params.Get("after")
    var afterJSON map[string][]int
    if afterJSON, err = fetchRunResultsJSONForParam(r, ctx, specAfter); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    } else if afterJSON == nil {
        http.Error(w, specAfter + " not found", http.StatusNotFound)
        return
    }

    diffJSON := diffResults(beforeJSON, afterJSON)
    var bytes []byte
    if bytes, err = json.Marshal(diffJSON); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Write(bytes)
}

type PlatformAtRevision struct {
    Platform string
    Revision string
}

func parsePlatformAtRevisionSpec(spec string) (platformAtRevision PlatformAtRevision, err error) {
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
    var browserNames []string
    if browserNames, err = getBrowserNames(); err != nil {
        return platformAtRevision, err
    }
    for _, name := range browserNames {
        if name == platformAtRevision.Platform {
            return platformAtRevision, nil
        }
    }
    return platformAtRevision, errors.New("Platform " + platformAtRevision.Platform + " not found")
}

func fetchRunResultsJSONForParam(
        r *http.Request, ctx context.Context, revision string) (results map[string][]int, err error) {
    var spec PlatformAtRevision
    if spec, err = parsePlatformAtRevisionSpec(revision); err != nil {
        return nil, err
    }
    return fetchRunResultsJSONForSpec(r, ctx, spec)
}

func fetchRunResultsJSONForSpec(
        r *http.Request, ctx context.Context, revision PlatformAtRevision) (results map[string][]int, err error) {
    var run TestRun
    if run, err = fetchRunForSpec(ctx, revision); err != nil {
        return nil, err
    } else if (run == TestRun{}) {
        return nil, nil
    }
    return fetchRunResultsJSON(r, ctx, run)
}

func fetchRunForSpec(ctx context.Context, revision PlatformAtRevision) (TestRun, error) {
    baseQuery := datastore.
    NewQuery("TestRun").
        Order("-CreatedAt").
        Limit(100)

    var results []TestRun
    query := baseQuery.
        Filter("BrowserName =", revision.Platform).
        Filter("Revision = ", revision.Revision)
    if _, err := query.GetAll(ctx, &results); err != nil {
        return TestRun{}, err
    }
    if len(results) < 1 {
        return TestRun{}, nil
    }
    return results[0], nil
}

func fetchRunResultsJSON(r *http.Request, ctx context.Context, run TestRun) (results map[string][]int, err error) {
    client := urlfetch.Client(ctx)
    url := run.ResultsURL
    if strings.Index(url, "/") == 0 {
        reqUrl := *r.URL
        reqUrl.Path = url
    }
    var resp *http.Response
    if resp, err = client.Get(url); err != nil {
        panic(url)
        return nil, err
    }
    defer resp.Body.Close()
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
            diff[test] = []int { resultsBefore[1], resultsBefore[1] }
        } else {
            passDiff := Abs(resultsBefore[0] - resultsAfter[0])
            countDiff := Abs(resultsBefore[1] - resultsAfter[1])
            if countDiff == 0 && passDiff == 0 {
                continue
            }
            diff[test] = []int { passDiff + countDiff, Max(resultsBefore[1], resultsAfter[1]) }
        }
    }
    for test, resultsAfter := range after {
        if _, ok := before[test]; !ok {
            // Missing? Then N / N tests are 'different'
            diff[test] = []int { resultsAfter[1], resultsAfter[1] }
        }
    }
    return diff
}

func Abs(x int) int { if x < 0 { return -x } else { return x } }
func Max(x int, y int) int { if x < y { return y } else { return x } }