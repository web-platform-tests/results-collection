// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package metrics

import (
	"fmt"
	"reflect"
	"strings"
)

// GetDatastoreKindName gets the full (namespaced) data type name for the given
// interface (whether a pointer or not).
func GetDatastoreKindName(data interface{}) string {
	dataType := reflect.TypeOf(data)
	for dataType.Kind() == reflect.Ptr {
		dataType = reflect.Indirect(reflect.ValueOf(
			data)).Type()
	}
	return fmt.Sprintf("%s.%s",
		strings.Replace(dataType.PkgPath(), "/", ".", -1),
		dataType.Name())
}
