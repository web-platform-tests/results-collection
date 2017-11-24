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

	"github.com/stretchr/testify/assert"
)

const mockTestPath = "/mock/path.html"

func TestDiffResults_NoDifference(t *testing.T) {
	assertNoDeltaDifferences(t, []int{0, 1}, []int{0, 1})
	assertNoDeltaDifferences(t, []int{3, 4}, []int{3, 4})
}

func TestDiffResults_Difference(t *testing.T) {
	// One test now passing
	assertDelta(t, []int{0, 1}, []int{1, 1}, []int{1, 1})

	// One test now failing
	assertDelta(t, []int{1, 1}, []int{0, 1}, []int{1, 1})

	// Two tests, one now failing
	assertDelta(t, []int{2, 2}, []int{1, 2}, []int{1, 2})

	// Three tests, two now passing
	assertDelta(t, []int{1, 3}, []int{3, 3}, []int{2, 3})
}

func TestDiffResults_Added(t *testing.T) {
	// One new test, all passing
	assertDelta(t, []int{1, 1}, []int{2, 2}, []int{1, 2})

	// One new test, all failing
	assertDelta(t, []int{0, 1}, []int{0, 2}, []int{1, 2})

	// One new test, new test passing
	assertDelta(t, []int{0, 1}, []int{1, 2}, []int{1, 2})

	// One new test, new test failing
	assertDelta(t, []int{1, 1}, []int{1, 2}, []int{1, 2})
}

func TestDiffResults_Removed(t *testing.T) {
	// One removed test, all passing
	assertDelta(t, []int{2, 2}, []int{1, 1}, []int{1, 2})

	// One removed test, all failing
	assertDelta(t, []int{0, 2}, []int{0, 1}, []int{1, 2})

	// One removed test, deleted test passing
	assertDelta(t, []int{1, 2}, []int{0, 1}, []int{1, 2})

	// One removed test, deleted test failing
	assertDelta(t, []int{1, 2}, []int{1, 1}, []int{1, 2})
}

func assertNoDeltaDifferences(t *testing.T, before []int, after []int) {
	rBefore, rAfter := getDeltaResultsMaps(before, after)
	assert.Equal(t, map[string][]int{}, diffResults(rBefore, rAfter))
}

func assertDelta(t *testing.T, before []int, after []int, delta []int) {
	rBefore, rAfter := getDeltaResultsMaps(before, after)
	assert.Equal(
		t,
		map[string][]int{mockTestPath: delta},
		diffResults(rBefore, rAfter))
}

func getDeltaResultsMaps(before []int, after []int) (map[string][]int, map[string][]int) {
	return map[string][]int{mockTestPath: before},
		map[string][]int{mockTestPath: after}
}
