// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package webapp

import (
	"encoding/json"
	"io/ioutil"
	"sort"

	models "github.com/w3c/wptdashboard/shared"
)

var browsers map[string]models.Browser

// No 'set' type in Go, so use map instead.
var browserNames map[string]bool
var browserNamesAlphabetical []string

// GetBrowsers loads, parses and returns the set of names of browsers
// which are to be included (flagged as initially_loaded in the JSON).
func GetBrowsers() (map[string]models.Browser, error) {
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
	if browserNamesAlphabetical == nil {
		if err := loadBrowserNames(); err != nil {
			return nil, err
		}
	}
	return browserNamesAlphabetical, nil
}

// IsBrowserName determines whether the given name string is a valid browser name.
// Used for validating user-input params for browsers.
func IsBrowserName(name string) bool {
	if browserNames == nil {
		if err := loadBrowserNames(); err != nil {
			return false
		}
	}
	_, ok := browserNames[name]
	return ok
}

func loadBrowserNames() error {
	var browsers map[string]models.Browser
	var err error
	if browsers, err = GetBrowsers(); err != nil {
		return err
	}
	browserNames = make(map[string]bool)
	for _, browser := range browsers {
		if browser.InitiallyLoaded {
			browserNamesAlphabetical = append(browserNamesAlphabetical, browser.BrowserName)
			browserNames[browser.BrowserName] = true
		}
	}
	sort.Strings(browserNamesAlphabetical)
	return nil
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}
func max(x int, y int) int {
	if x < y {
		return y
	}
	return x
}
