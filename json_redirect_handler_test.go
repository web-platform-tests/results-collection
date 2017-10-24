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
  "testing"
)

type Case struct {
  testRun TestRun
  testFile *string
  expected string
}

const sha = "abcdef0123"
const resultsURLBase = "https://storage.googleapis.com/wptd/" + sha + "/"
const platform = "chrome-63.0-linux"
const resultsURL = resultsURLBase + "/" + platform + "-summary.json.gz"

func TestGetResultsURL_NoTestFile(t *testing.T) {
    checkResult(
    t,
    Case {
      TestRun {
        ResultsURL: resultsURL,
        Revision: sha,
      },
      nil,
      resultsURL,
    })
}

func TestGetResultsURL_EmptyFile(t *testing.T) {
  emptyTestFile := ""
  checkResult(
    t,
    Case {
      TestRun {
        ResultsURL: resultsURL,
        Revision: sha,
      },
      &emptyTestFile,
      resultsURL,
    })
}

func TestGetResultsURL_TestFile(t *testing.T) {
  file := "css/vendor-imports/mozilla/mozilla-central-reftests/flexbox/flexbox-root-node-001b.html"
  checkResult(
    t,
    Case {
      TestRun {
        ResultsURL: resultsURL,
        Revision: sha,
      },
      &file,
      resultsURLBase + platform + "/" + file,
    })
}

func TestGetResultsURL_TrailingSlash(t *testing.T) {
  trailingSlash := "/"
  checkResult(
    t,
    Case {
      TestRun {
        ResultsURL: resultsURL,
        Revision: sha,
      },
      &trailingSlash,
      resultsURL,
    })
}

func checkResult(t *testing.T, c Case) {
    got := getResultsURL(c.testRun, c.testFile)
    if got != c.expected {
        t.Errorf("\nGot:\n%q\nExpected:\n%q", got, c.expected)
    }
}
