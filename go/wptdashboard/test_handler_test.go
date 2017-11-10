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
	"net/http/httptest"
	"testing"
)

func TestGetRunSHA(t *testing.T) {
	r := httptest.NewRequest("GET", "http://wpt.fyi/", nil)
	runSHA, err := GetRunSHA(r)
	assert.Nil(t, err)
	assert.Equal(t, "latest", runSHA)
}

func TestGetRunSHA_2(t *testing.T) {
	sha := "0123456789"
	r := httptest.NewRequest("GET", "http://wpt.fyi/?sha="+sha, nil)
	runSHA, err := GetRunSHA(r)
	assert.Nil(t, err)
	assert.Equal(t, sha, runSHA)
}

func TestGetRunSHA_BadRequest(t *testing.T) {
	r := httptest.NewRequest("GET", "http://wpt.fyi/?sha=%zz", nil)
	runSHA, err := GetRunSHA(r)
	assert.NotNil(t, err)
	assert.Equal(t, "latest", runSHA)
}

func TestGetRunSHA_NonSHA(t *testing.T) {
	r := httptest.NewRequest("GET", "http://wpt.fyi/?sha=123", nil)
	runSHA, err := GetRunSHA(r)
	assert.Nil(t, err)
	assert.Equal(t, "latest", runSHA)
}

func TestGetRunSHA_NonSHA_2(t *testing.T) {
	r := httptest.NewRequest("GET", "http://wpt.fyi/?sha=zapper0123", nil)
	runSHA, err := GetRunSHA(r)
	assert.Nil(t, err)
	assert.Equal(t, "latest", runSHA)
}
