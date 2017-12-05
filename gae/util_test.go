// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package wptdashboard

import (
	"github.com/stretchr/testify/assert"
	"sort"
	"testing"
)

func TestGetBrowserNames(t *testing.T) {
	names, _ := GetBrowserNames()
	assert.True(t, sort.StringsAreSorted(names))
}

func TestIsBrowserName(t *testing.T) {
	assert.True(t, IsBrowserName("chrome"))
	assert.True(t, IsBrowserName("edge"))
	assert.True(t, IsBrowserName("firefox"))
	assert.True(t, IsBrowserName("safari"))
	assert.False(t, IsBrowserName("not-a-browser"))
}

func TestIsBrowserName_Names(t *testing.T) {
	names, _ := GetBrowserNames()
	for _, name := range names {
		assert.True(t, IsBrowserName(name))
	}
}
