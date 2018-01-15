// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package compute

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"

	"github.com/w3c/wptdashboard/metrics"
	"github.com/w3c/wptdashboard/shared"
)

var timeA = time.Unix(0, 0)
var timeB = time.Unix(0, 1)
var runA = shared.TestRun{
	"ABrowser",
	"1.0",
	"MyOS",
	"1.0",
	"abcd",
	"http://example.com/a_run.json",
	timeA,
}
var runB = shared.TestRun{
	"BBrowser",
	"1.0",
	"MyOS",
	"1.0",
	"dcba",
	"http://example.com/b_run.json",
	timeB,
}

func TestGatherResultsById_TwoRuns_SameTest(t *testing.T) {
	testName := "Do a thing"
	results := &[]metrics.TestRunResults{
		{
			&runA,
			&metrics.TestResults{
				"A test",
				"OK",
				&testName,
				[]metrics.SubTest{},
			},
		},
		{
			&runB,
			&metrics.TestResults{
				"A test",
				"ERROR",
				&testName,
				[]metrics.SubTest{},
			},
		},
	}
	gathered := GatherResultsById(results)
	assert.Equal(t, 1, len(gathered)) // Merged to single TestId: {"A test",""}.
	for testId, runStatusMap := range gathered {
		assert.Equal(t, metrics.TestId{"A test", ""}, testId)
		assert.Equal(t, 2, len(runStatusMap))
		assert.Equal(t, metrics.CompleteTestStatus{
			metrics.TestStatus_fromString("OK"),
			metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
		}, runStatusMap[runA])
		assert.Equal(t, metrics.CompleteTestStatus{
			metrics.TestStatus_fromString("ERROR"),
			metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
		}, runStatusMap[runB])
	}
}

func TestGatherResultsById_TwoRuns_DiffTests(t *testing.T) {
	testName := "Do a thing"
	results := &[]metrics.TestRunResults{
		{
			&runA,
			&metrics.TestResults{
				"A test",
				"OK",
				&testName,
				[]metrics.SubTest{},
			},
		},
		{
			&runA,
			&metrics.TestResults{
				"Shared test",
				"ERROR",
				&testName,
				[]metrics.SubTest{},
			},
		},
		{
			&runB,
			&metrics.TestResults{
				"Shared test",
				"OK",
				&testName,
				[]metrics.SubTest{},
			},
		},
		{
			&runB,
			&metrics.TestResults{
				"B test",
				"ERROR",
				&testName,
				[]metrics.SubTest{},
			},
		},
	}
	gathered := GatherResultsById(results)
	assert.Equal(t, 3, len(gathered)) // A, Shared, B.
	assert.Equal(t, 1, len(gathered[metrics.TestId{"A test", ""}]))
	assert.Equal(t, metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("OK"),
		metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
	}, gathered[metrics.TestId{"A test", ""}][runA])
	assert.Equal(t, 2, len(gathered[metrics.TestId{"Shared test", ""}]))
	assert.Equal(t, metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("ERROR"),
		metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
	}, gathered[metrics.TestId{"Shared test", ""}][runA])
	assert.Equal(t, metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("OK"),
		metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
	}, gathered[metrics.TestId{"Shared test", ""}][runB])
	assert.Equal(t, 1, len(gathered[metrics.TestId{"B test", ""}]))
	assert.Equal(t, metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("ERROR"),
		metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
	}, gathered[metrics.TestId{"B test", ""}][runB])
}

func TestGatherResultsById_OneRun_SubTest(t *testing.T) {
	testName := "Do a thing"
	subName1 := "First sub-test"
	subName2 := "Second sub-test"
	subStatus1 := "A-OK!"
	subStatus2 := "Oops..."
	results := &[]metrics.TestRunResults{
		{
			&runA,
			&metrics.TestResults{
				"A test",
				"OK",
				&testName,
				[]metrics.SubTest{
					{
						subName1,
						"PASS",
						&subStatus1,
					},
					{
						subName2,
						"FAIL",
						&subStatus2,
					},
				},
			},
		},
	}
	gathered := GatherResultsById(results)
	assert.Equal(t, 3, len(gathered)) // Top-level test + 2 sub-tests.
	testIds := make([]metrics.TestId, 0, len(gathered))
	for testId, _ := range gathered {
		testIds = append(testIds, testId)
	}
	assert.ElementsMatch(t, [...]metrics.TestId{
		{"A test", ""},
		{"A test", subName1},
		{"A test", subName2},
	}, testIds)
	assert.Equal(t, metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("OK"),
		metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
	}, gathered[metrics.TestId{"A test", ""}][runA])
	assert.Equal(t, metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("OK"),
		metrics.SubTestStatus_fromString("PASS"),
	}, gathered[metrics.TestId{"A test", subName1}][runA])
	assert.Equal(t, metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("OK"),
		metrics.SubTestStatus_fromString("FAIL"),
	}, gathered[metrics.TestId{"A test", subName2}][runA])
}

func TestComputeTotals(t *testing.T) {
	statusz := make(TestRunsStatus)
	status1 := metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("OK"),
		metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
	}
	status2 := metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("ERROR"),
		metrics.SubTestStatus_fromString("STATUS_UNKNOWN"),
	}
	subStatus1 := metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("OK"),
		metrics.SubTestStatus_fromString("PASS"),
	}
	subStatus2 := metrics.CompleteTestStatus{
		metrics.TestStatus_fromString("OK"),
		metrics.SubTestStatus_fromString("NOT_RUN"),
	}
	ab1 := metrics.TestId{"a/b/1", ""}
	ab2 := metrics.TestId{"a/b/2", ""}
	ac1 := metrics.TestId{"a/c/1", ""}
	ac1x := metrics.TestId{"a/c/1", "x"}
	ac1y := metrics.TestId{"a/c/1", "y"}
	ac1z := metrics.TestId{"a/c/1", "z"}
	statusz[ab1] = make(map[shared.TestRun]metrics.CompleteTestStatus)
	statusz[ab2] = make(map[shared.TestRun]metrics.CompleteTestStatus)
	statusz[ac1] = make(map[shared.TestRun]metrics.CompleteTestStatus)
	statusz[ac1x] = make(map[shared.TestRun]metrics.CompleteTestStatus)
	statusz[ac1y] = make(map[shared.TestRun]metrics.CompleteTestStatus)
	statusz[ac1z] = make(map[shared.TestRun]metrics.CompleteTestStatus)
	statusz[ab1][runA] = status1
	statusz[ab1][runB] = status2
	statusz[ab2][runB] = status1
	statusz[ac1][runA] = status1
	statusz[ac1x][runA] = subStatus1
	statusz[ac1y][runA] = subStatus2
	statusz[ac1z][runA] = subStatus2

	totals := ComputeTotals(&statusz)
	assert.Equal(t, 6, len(totals))   // a, a/b, a/c, a/b/1, a/b/2, a/c/1.
	assert.Equal(t, 6, totals["a"])   // a/b/1, a/b/2, a/c/1, a/c/1:x, a/c/1:y, a/c/1:z.
	assert.Equal(t, 2, totals["a/b"]) // a/b/1, a/b/2.
	assert.Equal(t, 1, totals["a/b/1"])
	assert.Equal(t, 1, totals["a/b/2"])
	assert.Equal(t, 4, totals["a/c"])   // a/c/1, a/c/1:x, a/c/1:y, a/c/1:z.
	assert.Equal(t, 4, totals["a/c/1"]) // a/c/1, a/c/1:x, a/c/1:y, a/c/1:z.
}
