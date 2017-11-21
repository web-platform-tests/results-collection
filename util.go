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
	"io/ioutil"
	"sort"
)

var browsers map[string]Browser
var browserNames []string

// GetBrowsers loads, parses and returns the set of names of browsers
// which are to be included (flagged as initially_loaded in the JSON).
func GetBrowsers() (map[string]Browser, error) {
	if browsers != nil {
		return browsers, nil
	}
	var bytes []byte
	var err error
	if bytes, err = ioutil.ReadFile("browsers.json"); err != nil {
		return nil, err
	}

	if err = json.Unmarshal(bytes, &browsers); err != nil {
		return nil, err
	}
	return browsers, nil
}

// GetBrowserNames returns an alphabetically-ordered array of the names
// of the browsers returned by GetBrowsers.
func GetBrowserNames() ([]string, error) {
	if browserNames != nil {
		return browserNames, nil
	}

	var browsers map[string]Browser
	var err error
	if browsers, err = GetBrowsers(); err != nil {
		return nil, err
	}
	for _, browser := range browsers {
		if browser.InitiallyLoaded {
			browserNames = append(browserNames, browser.BrowserName)
		}
	}
	sort.Strings(browserNames)
	return browserNames, nil
}
