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

package compute

import (
	"log"
	"strings"

	"github.com/w3c/wptdashboard/metrics"
	base "github.com/w3c/wptdashboard/shared"
)

type TestRunsStatus map[metrics.TestId]map[base.TestRun]metrics.CompleteTestStatus

// Type for decision problem: "What does it mean for a test result to 'pass'"?
type Passes func(*metrics.CompleteTestStatus) bool

//
// Passes functions
//

func OkAndUnknownOrPasses(status *metrics.CompleteTestStatus) bool {
	return status.Status == metrics.TestStatus_TEST_OK &&
		(status.SubStatus ==
			metrics.SubTestStatus_SUB_TEST_STATUS_UNKNOWN ||
			status.SubStatus == metrics.SubTestStatus_SUB_TEST_PASS)
}

// Gather results from test runs into input format for Compute* functions in
// this module.
func GatherResultsById(allResults *[]metrics.TestRunResults) (
	resultsById TestRunsStatus) {
	resultsById = make(TestRunsStatus)

	for _, results := range *allResults {
		result := results.Res
		run := *results.Run
		testId := metrics.TestId{Test: result.Test}
		_, ok := resultsById[testId]
		if !ok {
			resultsById[testId] = make(
				map[base.TestRun]metrics.CompleteTestStatus)

		}
		_, ok = resultsById[testId][run]
		if ok {
			log.Printf("Duplicate results for TestId:%v  in "+
				"TestRun:%v.  Overwriting.\n", testId, run)
		}
		newStatus := metrics.CompleteTestStatus{
			Status: metrics.TestStatus_fromString(result.Status),
		}
		resultsById[testId][run] = newStatus

		for _, subResult := range result.Subtests {
			testId := metrics.TestId{
				Test: result.Test,
				Name: subResult.Name,
			}
			_, ok := resultsById[testId]
			if !ok {
				resultsById[testId] = make(
					map[base.TestRun]metrics.CompleteTestStatus)
			}
			_, ok = resultsById[testId][run]
			if ok {
				log.Printf("Duplicate sub-results for "+
					"TestId:%v  in TestRun:%v.  "+
					"Overwriting.\n", testId, run)
			}
			newStatus := metrics.CompleteTestStatus{
				Status: metrics.TestStatus_fromString(
					result.Status),
				SubStatus: metrics.SubTestStatus_fromString(
					subResult.Status),
			}
			resultsById[testId][run] = newStatus
		}
	}

	return resultsById
}

// Compute {"test/path": number of tests} for all test directory and/or file
// names included in results.
func ComputeTotals(results *TestRunsStatus) (metrics map[string]int) {
	metrics = make(map[string]int)

	for testId := range *results {
		pathParts := strings.Split(testId.Test, "/")
		for i := range pathParts {
			subPath := strings.Join(pathParts[:i+1], "/")
			_, ok := metrics[subPath]
			if !ok {
				metrics[subPath] = 0
			}
			metrics[subPath] = metrics[subPath] + 1
		}
	}

	return metrics
}

// Compute:
// [
//  [TestIds of tests browserName + 0 other browsers fail],
//  [TestIds of tests browserName + 1 other browsers fail],
//  ...
//  [TestIds of tests browserName + n other browsers fail],
// ]
func ComputeBrowserFailureList(numRuns int, browserName string,
	results *TestRunsStatus, passes Passes) (failures [][]*metrics.TestId) {
	failures = make([][]*metrics.TestId, numRuns)

	for testId, runStatuses := range *results {
		numOtherFailures := 0
		browserFailed := false
		for run, status := range runStatuses {
			if !passes(&status) {
				if run.BrowserName == browserName {
					browserFailed = true
				} else {
					numOtherFailures++
				}
			}
		}
		if !browserFailed {
			continue
		}
		failures[numOtherFailures] = append(failures[numOtherFailures],
			&testId)
	}

	return failures
}

// Compute:
// {
//   "test/path": [
//     Number of tests passed by 0 test runs,
//     Number of tests passed by 1 test run,
//     Number of tests passed by 2 test runs,
//     ...
//     Number of tests passed by n test runs,
//   ],
// }
func ComputePassRateMetric(numRuns int,
	results *TestRunsStatus, passes Passes) (
	metrics map[string][]int) {
	metrics = make(map[string][]int)

	for testId, runStatuses := range *results {
		passCount := 0
		for _, status := range runStatuses {
			if passes(&status) {
				passCount++
			}
		}
		pathParts := strings.Split(testId.Test, "/")
		for i := range pathParts {
			subPath := strings.Join(pathParts[:i+1], "/")
			_, ok := metrics[subPath]
			if !ok {
				metrics[subPath] = make([]int, numRuns+1)
			}
			metrics[subPath][passCount] =
				metrics[subPath][passCount] + 1
		}
	}

	return metrics
}
