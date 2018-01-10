// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package metrics

import (
	"github.com/stretchr/testify/assert"
	"testing"
)

func TestGetDatastoreKindName(t *testing.T) {
	testId := TestId{
		Test: "test",
		Name: "name",
	}

	const expected = "github.com.w3c.wptdashboard.metrics.TestId"
	name := GetDatastoreKindName(testId)
	assert.Equal(t, expected, name)

	name = GetDatastoreKindName(&testId)
	assert.Equal(t, expected, name)
}
