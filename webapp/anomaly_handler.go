// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package webapp

import (
	"net/http"
)

// anomalyHandler handles the view of test results showing which tests pass in
// some, but not all, browsers.
func anomalyHandler(w http.ResponseWriter, r *http.Request) {
	// Empty struct placeholder.
	data := struct{}{}
	if err := templates.ExecuteTemplate(w, "anomalies.html", data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}
