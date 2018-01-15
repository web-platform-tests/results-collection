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

func TestGatherResultsById_TwoRuns_SameTest(t *testing.T) {
	runA := shared.TestRun{
		"ABrowser",
		"1.0",
		"MyOS",
		"1.0",
		"abcd",
		"http://example.com/a_run.json",
		timeA,
	}
	runB := shared.TestRun{
		"BBrowser",
		"1.0",
		"MyOS",
		"1.0",
		"dcba",
		"http://example.com/b_run.json",
		timeB,
	}
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
