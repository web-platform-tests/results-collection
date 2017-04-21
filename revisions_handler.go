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

package wptdashboard

import (
    "appengine"
    "appengine/datastore"
    "net/http"
)

func revisionsHandler(w http.ResponseWriter, r *http.Request) {
    ctx := appengine.NewContext(r)
    var revisions []WPTRevision
    q := datastore.NewQuery("WPTRevision").Order("-Number").Limit(50)

    if _, err := q.GetAll(ctx, &revisions); err != nil {
            http.Error(w, err.Error(), http.StatusInternalServerError)
    }

    if err := templates.ExecuteTemplate(w, "revisions.html", revisions); err != nil {
            http.Error(w, err.Error(), http.StatusInternalServerError)
    }
}
