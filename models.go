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
)

type WPTRevision struct {
    // This is not the number of commits since the first commit
    // in WPT. It is meant to be a monotonically increasing number
    // incremented by the WPT revision updater daily cron job.
    // It is then used to fetch the latest SubTestResults.
    Number          int

    // The Retain flag defaults to false, but if
    // marked true it signals to the data pruner
    // not to delete results under this WPT revision.
    Retain          bool
}

func getCurrentWPTRevision(ctx appengine.Context) ([]*datastore.Key, error) {
    // var wptRevision []WPTRevision
    // var keys []datastore.Key
    q := datastore.NewQuery("WPTRevision").Order("-Number").Limit(1).KeysOnly()
    keys, err := q.GetAll(ctx, nil)
    ctx.Debugf("Done processing results")
    return keys, err
}
