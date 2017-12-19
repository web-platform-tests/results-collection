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

package storage

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"io/ioutil"
	"log"
	"sort"
	"strings"
	"sync"

	"cloud.google.com/go/storage"
	tm "github.com/buger/goterm"
	"github.com/w3c/wptdashboard/metrics"
	base "github.com/w3c/wptdashboard/shared"
	"golang.org/x/net/context"
	"google.golang.org/api/iterator"
)

// Encapsulate bucket name and handle; both are needed for some storage
// read/write routines.
type Bucket struct {
	Name   *string
	Handle *storage.BucketHandle
}

// Encapsulate info required to read from or write to a storage bucket.
type Context struct {
	Context context.Context
	Client  *storage.Client
	Bucket  *Bucket
}

// Upload metricsRunData as objName in bucket via client in context.
func UploadMetricsRunData(ctx *Context, objName *string,
	metricsRunData *metrics.MetricsRunData) (err error) {

	log.Println("Writing " + *objName + " to Google Cloud Storage")
	obj := ctx.Bucket.Handle.Object(*objName)
	objWriter := obj.NewWriter(ctx.Context)
	defer objWriter.Close()
	gzWriter := gzip.NewWriter(objWriter)
	defer gzWriter.Close()
	encoder := json.NewEncoder(gzWriter)
	err = encoder.Encode(metricsRunData)
	if err != nil {
		log.Printf("Error writing %s to Google Cloud Storage: %v\n",
			*objName, err)
		return err
	}
	log.Println("Wrote " + *objName + " to Google Cloud Storage")

	return err
}

// Load (test run, test results) pairs for given test runs. Use client in
// context to load data from bucket.
func LoadTestRunResults(ctx *Context, runs []base.TestRun) (
	runResults []metrics.TestRunResults) {
	resultChan := make(chan metrics.TestRunResults, 0)
	errChan := make(chan error, 0)
	runResults = make([]metrics.TestRunResults, 0, 100000)

	go func() {
		defer close(resultChan)
		defer close(errChan)

		var wg sync.WaitGroup
		wg.Add(len(runs))
		for _, run := range runs {
			go func(run base.TestRun) {
				defer wg.Done()
				processTestRun(ctx, &run, resultChan, errChan)
			}(run)
		}
		wg.Wait()
	}()

	progress := make(map[base.TestRun]int)
	type Nothing struct{}

	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		for results := range resultChan {
			runResults = append(runResults, results)

			testRunPtr := results.Run
			testRun := *testRunPtr
			if _, ok := progress[testRun]; !ok {
				progress[testRun] = 0
			}
			progress[testRun] = progress[testRun] + 1

			keys := make(metrics.TestRunSlice, 0, len(progress))
			for key := range progress {
				keys = append(keys, key)
			}
			sort.Sort(keys)

			tm.Clear()
			tm.MoveCursor(1, 1)
			for _, run := range keys {
				count := progress[run]
				tm.Printf("%10s %10s %10s %10s %10s :: %10d\n",
					run.Revision, run.BrowserName,
					run.BrowserVersion, run.OSName,
					run.OSVersion, count)
			}
			tm.Flush()
		}
	}()
	go func() {
		defer wg.Done()
		for err := range errChan {
			log.Fatal(err)
		}
	}()
	wg.Wait()

	return runResults
}

func processTestRun(ctx *Context, testRun *base.TestRun,
	resultChan chan metrics.TestRunResults, errChan chan error) {
	resultsURL := testRun.ResultsURL

	// summaryURL format:
	//
	// protocol://host/bucket/dir/path-summary.json.gz
	//
	// where results are stored in
	//
	// protocol://host/bucket/dir/path/**
	//
	// Desired bucket-relative GCS prefix:
	//
	// dir/path/
	prefixSliceStart := strings.Index(resultsURL, *ctx.Bucket.Name) +
		len(*ctx.Bucket.Name) + 1
	prefixSliceEnd := strings.LastIndex(resultsURL, "-")
	prefix := resultsURL[prefixSliceStart:prefixSliceEnd] + "/"

	// Get objects with desired prefix, process them in parallel, then
	// return.
	it := ctx.Bucket.Handle.Objects(ctx.Context, &storage.Query{
		Prefix: prefix,
	})
	var wg sync.WaitGroup
	wg.Add(1)

	for {
		var err error
		attrs, err := it.Next()
		if err == iterator.Done {
			break
		}
		if err != nil {
			errChan <- err
			continue
		}

		// Skip directories.
		if attrs.Name == "" {
			continue
		}

		wg.Add(1)
		go func() {
			defer wg.Done()
			loadTestResults(ctx, testRun, attrs.Name, resultChan,
				errChan)
		}()
	}
	wg.Done()
	wg.Wait()
}

func loadTestResults(ctx *Context, testRun *base.TestRun, objName string,
	resultChan chan metrics.TestRunResults, errChan chan error) {
	// Read object from GCS
	obj := ctx.Bucket.Handle.Object(objName)
	reader, err := obj.NewReader(ctx.Context)
	if err != nil {
		errChan <- err
		return
	}
	defer reader.Close()
	data, err := ioutil.ReadAll(reader)
	if err != nil {
		errChan <- err
		return
	}

	// Unmarshal JSON, which may be gzipped.
	var results metrics.TestResults
	var anyResult interface{}
	if err := json.Unmarshal(data, &anyResult); err != nil {
		reader2 := bytes.NewReader(data)
		reader3, err := gzip.NewReader(reader2)
		if err != nil {
			errChan <- err
			return
		}
		defer reader3.Close()
		unzippedData, err := ioutil.ReadAll(reader3)
		if err != nil {
			errChan <- err
			return
		}
		if err := json.Unmarshal(unzippedData, &results); err != nil {
			errChan <- err
			return
		}
		resultChan <- metrics.TestRunResults{testRun, &results}
	} else {
		if err := json.Unmarshal(data, &results); err != nil {
			errChan <- err
			return
		}
		resultChan <- metrics.TestRunResults{testRun, &results}
	}
}
