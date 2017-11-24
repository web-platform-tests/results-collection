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
	"strings"
	"testing"

	"github.com/deckarep/golang-set"
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

func TestDiffResults_Filtered(t *testing.T) {
	// Test filtering by each /, /mock/, and /mock/path.html
	pieces := strings.SplitAfter(mockTestPath, "/")
	for i := 1; i < len(pieces); i++ {
		paths := mapset.NewSet(strings.Join(pieces[:i], ""))
		assertDeltaFiltered(t, []int{0, 5}, []int{5, 5}, []int{5, 5}, paths)
	}

	// Filter where none match
	paths := mapset.NewSet("/different/path/")
	rBefore, rAfter := getDeltaResultsMaps([]int{0, 5}, []int{5, 5})
	assert.Empty(t, diffResults(rBefore, rAfter, paths))

	// Filter where one matches
	mockPath1, mockPath2 := "/mock/path-1.html", "/mock/path-2.html"
	rBefore = map[string][]int{
		mockPath1: {0, 1},
		mockPath2: {0, 1},
	}
	rAfter = map[string][]int{
		mockPath1: {2, 2},
		mockPath2: {2, 2},
	}
	paths = mapset.NewSet(mockPath1)
	delta := diffResults(rBefore, rAfter, paths)
	assert.NotContains(t, delta, mockPath2)
	assert.Contains(t, delta, mockPath1)
	assert.Equal(t, []int{2, 2}, delta[mockPath1])
}

func assertNoDeltaDifferences(t *testing.T, before []int, after []int) {
	rBefore, rAfter := getDeltaResultsMaps(before, after)
	assert.Equal(t, map[string][]int{}, diffResults(rBefore, rAfter, nil))
}

func assertDelta(t *testing.T, before []int, after []int, delta []int) {
	assertDeltaFiltered(t, before, after, delta, nil)
}

func assertDeltaFiltered(t *testing.T, before []int, after []int, delta []int, paths mapset.Set) {
	rBefore, rAfter := getDeltaResultsMaps(before, after)
	assert.Equal(
		t,
		map[string][]int{mockTestPath: delta},
		diffResults(rBefore, rAfter, paths))
}

func getDeltaResultsMaps(before []int, after []int) (map[string][]int, map[string][]int) {
	return map[string][]int{mockTestPath: before},
		map[string][]int{mockTestPath: after}
}
