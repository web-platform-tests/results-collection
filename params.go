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
// limitations under the License.package wptdashboard

package wptdashboard

import (
	"fmt"
	"net/http"
	"net/url"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"github.com/deckarep/golang-set"
)

// MaxCountDefaultValue is the default value returned by ParseMaxCountParam for the max-count param.
const MaxCountDefaultValue = 1

// MaxCountMaxValue is the maximum allowed value for the max-count param.
const MaxCountMaxValue = 500

// MaxCountMinValue is the minimum allowed value for the max-count param.
const MaxCountMinValue = 1

// SHARegex is a regex for SHA[0:10] slice of a git hash.
var SHARegex = regexp.MustCompile("[0-9a-fA-F]{10}")

// ParseSHAParam parses and validates the 'sha' param for the request.
// It returns "latest" by default (and in error cases).
func ParseSHAParam(r *http.Request) (runSHA string, err error) {
	// Get the SHA for the run being loaded (the first part of the path.)
	runSHA = "latest"
	params, err := url.ParseQuery(r.URL.RawQuery)
	if err != nil {
		return runSHA, err
	}

	runParam := params.Get("sha")
	if SHARegex.MatchString(runParam) {
		runSHA = runParam
	}
	return runSHA, err
}

// ParseBrowserParam parses and validates the 'browser' param for the request.
// It returns "" by default (and in error cases).
func ParseBrowserParam(r *http.Request) (browser string, err error) {
	browser = r.URL.Query().Get("browser")
	if "" == browser {
		return "", nil
	}
	if IsBrowserName(browser) {
		return browser, nil
	}
	return "", fmt.Errorf("invalid browser param %s", browser)
}

// ParseBrowsersParam returns a sorted list of browsers to include.
// It parses the 'browsers' parameter, split on commas, and also checks for the (repeatable) 'browser' params,
// before falling back to the default set of browsers.
func ParseBrowsersParam(r *http.Request) (browsers []string, err error) {
	browsers = r.URL.Query()["browser"]
	if browsersParam := r.URL.Query().Get("browsers"); browsersParam != "" {
		browsers = append(browsers, strings.Split(browsersParam, ",")...)
	}
	// If no params found, return the default.
	var browserNames []string
	if browserNames, err = GetBrowserNames(); err != nil {
		return nil, err
	}
	if len(browsers) == 0 {
		return browserNames, nil
	}
	// Otherwise filter to valid browser names.
	for i := 0; i < len(browsers); {
		if !IsBrowserName(browsers[i]) {
			// 'Remove' browser by switching to end and cropping.
			browsers[len(browsers)-1], browsers[i] = browsers[i], browsers[len(browsers)-1]
			browsers = browsers[:len(browsers)-1]
			continue
		}
		i++
	}
	sort.Strings(browsers)
	return browsers, nil
}

// ParseMaxCountParam parses the 'max-count' parameter as an integer.
func ParseMaxCountParam(r *http.Request) (count int, err error) {
	count = MaxCountDefaultValue
	if maxCountParam := r.URL.Query().Get("max-count"); maxCountParam != "" {
		if count, err = strconv.Atoi(maxCountParam); err != nil {
			return MaxCountDefaultValue, err
		}
		if count < MaxCountMinValue {
			count = MaxCountMinValue
		}
		if count > MaxCountMaxValue {
			count = MaxCountMaxValue
		}
	}
	return count, err
}

// ParsePathsParam returns a set list of test paths to include, or nil if no filter is provided (and all tests should be
// included). It parses the 'paths' parameter, split on commas, and also checks for the (repeatable) 'path' params.
func ParsePathsParam(r *http.Request) (paths mapset.Set) {
	pathParams := r.URL.Query()["path"]
	pathsParam := r.URL.Query().Get("paths")
	if len(pathParams) == 0 && pathsParam == "" {
		return nil
	}

	paths = mapset.NewSet()
	for _, path := range pathParams {
		paths.Add(path)
	}
	if browsersParam := pathsParam; browsersParam != "" {
		for _, path := range strings.Split(browsersParam, ",") {
			paths.Add(path)
		}
	}
	return paths
}
