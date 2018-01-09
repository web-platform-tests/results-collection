// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package metrics

import (
	"time"

	base "github.com/w3c/wptdashboard/shared"
)

//
// Sortable slices of test runs
//
type TestRunSlice []base.TestRun

func (s TestRunSlice) Len() int {
	return len(s)
}

func (s TestRunSlice) Less(i int, j int) bool {
	if s[i].Revision < s[j].Revision {
		return true
	}
	if s[i].Revision > s[j].Revision {
		return false
	}
	if s[i].BrowserName < s[j].BrowserName {
		return true
	}
	if s[i].BrowserName > s[j].BrowserName {
		return false
	}
	if s[i].BrowserVersion < s[j].BrowserVersion {
		return true
	}
	if s[i].BrowserVersion > s[j].BrowserVersion {
		return false
	}
	if s[i].OSName < s[j].OSName {
		return true
	}
	if s[i].OSName > s[j].OSName {
		return false
	}
	return s[i].OSVersion < s[j].OSVersion
}

func (s TestRunSlice) Swap(i int, j int) {
	s[i], s[j] = s[j], s[i]
}

type SubTest struct {
	Name    string  `json:"name"`
	Status  string  `json:"status"`
	Message *string `json:"message"`
}

type TestResults struct {
	Test     string    `json:"test"`
	Status   string    `json:"status"`
	Message  *string   `json:"message"`
	Subtests []SubTest `json:"subtests"`
}

type TestRunResults struct {
	Run *base.TestRun
	Res *TestResults
}

type TestId struct {
	Test string `json:"test"`
	Name string `json:"name"`
}

type TestIdSlice []TestId

func (s TestIdSlice) Len() int {
	return len(s)
}

func (s TestIdSlice) Less(i int, j int) bool {
	if s[i].Test < s[j].Test {
		return true
	}
	if s[i].Test > s[j].Test {
		return false
	}
	return s[i].Name < s[j].Name
}

func (s TestIdSlice) Swap(i int, j int) {
	s[i], s[j] = s[j], s[i]
}

// Enum: Test status, according to legitimate string values in WPT results
// reports.
type TestStatus int32

const (
	TestStatus_TEST_STATUS_UNKNOWN TestStatus = 0
	TestStatus_TEST_OK             TestStatus = 1
	TestStatus_TEST_ERROR          TestStatus = 2
	TestStatus_TEST_TIMEOUT        TestStatus = 3
)

var TestStatus_name = map[int32]string{
	0: "TEST_STATUS_UNKNOWN",
	1: "TEST_OK",
	2: "TEST_ERROR",
	3: "TEST_TIMEOUT",
}
var TestStatus_value = map[string]int32{
	"TEST_STATUS_UNKNOWN": 0,
	"TEST_OK":             1,
	"TEST_ERROR":          2,
	"TEST_TIMEOUT":        3,
}

func TestStatus_fromString(str string) (ts TestStatus) {
	value, ok := TestStatus_value["TEST_"+str]
	if !ok {
		return TestStatus_TEST_STATUS_UNKNOWN
	}
	return TestStatus(value)
}

// Enum: Sub-test status, according to legitimate string values in WPT
// results reports.
type SubTestStatus int32

const (
	SubTestStatus_SUB_TEST_STATUS_UNKNOWN SubTestStatus = 0
	SubTestStatus_SUB_TEST_PASS           SubTestStatus = 1
	SubTestStatus_SUB_TEST_FAIL           SubTestStatus = 2
	SubTestStatus_SUB_TEST_TIMEOUT        SubTestStatus = 3
	SubTestStatus_SUB_TEST_NOT_RUN        SubTestStatus = 4
)

// Copied from generated/sub_test_status.pb.go.
var SubTestStatus_name = map[int32]string{
	0: "SUB_TEST_STATUS_UNKNOWN",
	1: "SUB_TEST_PASS",
	2: "SUB_TEST_FAIL",
	3: "SUB_TEST_TIMEOUT",
	4: "SUB_TEST_NOT_RUN",
}
var SubTestStatus_value = map[string]int32{
	"SUB_TEST_STATUS_UNKNOWN": 0,
	"SUB_TEST_PASS":           1,
	"SUB_TEST_FAIL":           2,
	"SUB_TEST_TIMEOUT":        3,
	"SUB_TEST_NOT_RUN":        4,
}

func SubTestStatus_fromString(str string) (ts SubTestStatus) {
	value, ok := SubTestStatus_value["SUB_TEST_"+str]
	if !ok {
		return SubTestStatus_SUB_TEST_STATUS_UNKNOWN
	}
	return SubTestStatus(value)
}

//
// Intermediate state representations for metrics computation
//

type CompleteTestStatus struct {
	Status    TestStatus
	SubStatus SubTestStatus
}

type TestRunStatus struct {
	Run    *base.TestRun
	Status CompleteTestStatus
}

type PassRateMetadata struct {
	StartTime time.Time      `json:"start_time"`
	EndTime   time.Time      `json:"end_time"`
	TestRuns  []base.TestRun `json:"test_runs"`
	DataUrl   string         `json:"url"`
}

type FailuresMetadata struct {
	StartTime   time.Time      `json:"start_time"`
	EndTime     time.Time      `json:"end_time"`
	TestRuns    []base.TestRun `json:"test_runs"`
	DataUrl     string         `json:"url"`
	BrowserName string         `json:"browser_name"`
}

// Output type for metrics: Include runs as metadata, and arbitrary content
// as data.
type MetricsRunData struct {
	Metadata interface{} `json:"metadata"`
	Data     interface{} `json:"data"`
}
