// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package storage

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
	"reflect"
	"sort"
	"strings"
	"sync"

	"cloud.google.com/go/bigquery"
	"cloud.google.com/go/datastore"
	"cloud.google.com/go/storage"
	tm "github.com/buger/goterm"
	"github.com/w3c/wptdashboard/metrics"
	base "github.com/w3c/wptdashboard/shared"
	"golang.org/x/net/context"
	"google.golang.org/api/iterator"
)

type OutputLocation struct {
	GCSObjectPath string
	BQDatasetName string
	BQTableName   string
}

type OutputId struct {
	MetadataLocation OutputLocation
	DataLocation     OutputLocation
}

type Outputter interface {
	Output(OutputId, interface{}, []interface{}) (interface{}, []interface{}, []error)
}

// Encapsulate bucket name and handle; both are needed for some storage
// read/write routines.
type Bucket struct {
	Name   string
	Handle *storage.BucketHandle
}

// Encapsulate info required to read from or write to a storage bucket.
type GCSDatastoreContext struct {
	Context context.Context
	Bucket  Bucket
	Client  *datastore.Client
}

type GCSData struct {
	Metadata interface{}   `json:"metadata"`
	Data     []interface{} `json:"data"`
}

type BQDataset struct {
	Name    string
	Dataset *bigquery.Dataset
}

type BQTable struct {
	Name  string
	Table *bigquery.Table
}

type BQCollection struct {
	Dataset BQDataset
	Table   BQTable
}

type BQContext struct {
	Context context.Context
	Client  *bigquery.Client
}

func (ctx GCSDatastoreContext) Output(id OutputId, metadata interface{},
	data []interface{}) (
	metadataWritten interface{}, dataWritten []interface{}, errs []error) {
	name := fmt.Sprintf("%s/%s", ctx.Bucket.Name,
		id.DataLocation.GCSObjectPath)
	log.Printf("Writing %s to Google Cloud Storage\n", name)
	gcsData := GCSData{metadata, data}
	obj := ctx.Bucket.Handle.Object(id.DataLocation.GCSObjectPath)
	if err := func() error {
		objWriter := obj.NewWriter(ctx.Context)
		gzWriter := gzip.NewWriter(objWriter)
		encoder := json.NewEncoder(gzWriter)

		objWriter.ContentType = "application/json"
		objWriter.ContentEncoding = "gzip"

		if err := encoder.Encode(gcsData); err != nil {
			objWriter.CloseWithError(err)
			return err
		}

		if err := gzWriter.Close(); err != nil {
			return err
		}
		return objWriter.Close()
	}(); err != nil {
		log.Printf("Error writing %s to Google Cloud Storage: %v\n",
			name, err)
		errs = append(errs, err)
		return nil, make([]interface{}, 0), errs
	}
	log.Printf("Wrote %s to Google Cloud Storage\n", name)

	dataWritten = data

	log.Printf("Writing %s to Datastore\n", name)
	metadataType := reflect.TypeOf(metadata)
	for metadataType.Kind() == reflect.Ptr {
		metadataType = reflect.Indirect(reflect.ValueOf(
			metadata)).Type()
	}
	metadataKindName := fmt.Sprintf("%s.%s",
		strings.Replace(metadataType.PkgPath(), "/", ".", -1),
		metadataType.Name())
	metadataKey := datastore.IncompleteKey(metadataKindName, nil)

	// TODO: This is terrible, but Datastore doesn't use reflection, so the
	// metadata must be of a concrete struct type.
	var err error
	passRateMetadata, ok := metadata.(*metrics.PassRateMetadata)
	if !ok {
		failuresMetadata, ok := metadata.(*metrics.FailuresMetadata)
		if !ok {
			return nil, make([]interface{}, 0), []error{
				errors.New("Unknown metadata type"),
			}
		}
		_, err = ctx.Client.Put(ctx.Context, metadataKey,
			failuresMetadata)
	} else {
		_, err = ctx.Client.Put(ctx.Context, metadataKey,
			passRateMetadata)
	}
	if err != nil {
		log.Printf("Error writing %s to Datastore: %v\n",
			name, err)
		errs = append(errs, err)
		return nil, dataWritten, errs
	}
	log.Printf("Wrote %s to Google Cloud Storage\n", name)

	metadataWritten = metadata

	return metadataWritten, dataWritten, errs
}

func (ctx BQContext) Output(id OutputId, metadata interface{},
	data []interface{}) (metadataWritten interface{},
	dataWritten []interface{}, errs []error) {
	dataName := fmt.Sprintf("%s.%s", id.DataLocation.BQDatasetName,
		id.DataLocation.BQTableName)
	metadataName := fmt.Sprintf("%s.%s",
		id.MetadataLocation.BQDatasetName,
		id.MetadataLocation.BQTableName)
	log.Printf("Writing data to %s, %s BigQuery tables\n", dataName,
		metadataName)

	dataDataset := ctx.Client.Dataset(id.DataLocation.BQDatasetName)
	dataTable := dataDataset.Table(id.DataLocation.BQTableName)
	metadataDataset := ctx.Client.Dataset(id.MetadataLocation.BQDatasetName)
	metadataTable := dataDataset.Table(id.MetadataLocation.BQTableName)

	if err := dataDataset.Create(ctx.Context, nil); err != nil {
		log.Printf("Error creating BigQuery dataset %s for data (continuing anyway): %v\n",
			id.DataLocation.BQDatasetName, err)
	}
	if err := metadataDataset.Create(ctx.Context, nil); err != nil {
		log.Printf("Error creating BigQuery dataset %s for metadata (continuing anyway): %v\n",
			id.MetadataLocation.BQDatasetName, err)
	}

	metadataSchema, err := bigquery.InferSchema(metadata)
	if err != nil {
		log.Printf("Error creating BigQuery schema for metadata: %v\n",
			err)
		errs = append(errs, err)
		return metadataWritten, dataWritten, errs
	}
	dataSchema, err := bigquery.InferSchema(data[0])
	if err != nil {
		log.Printf("Error creating BigQuery schema for data: %v\n",
			err)
		errs = append(errs, err)
		return metadataWritten, dataWritten, errs
	}

	if err := dataTable.Create(ctx.Context, &bigquery.TableMetadata{
		Schema: dataSchema,
	}); err != nil {
		log.Printf("Error creating BigQuery table %s for data (continuing anyway): %v\n",
			dataName, err)
	}
	if err := metadataTable.Create(ctx.Context, &bigquery.TableMetadata{
		Schema: metadataSchema,
	}); err != nil {
		log.Printf("Error creating BigQuery table %s for metadata (continuing anyway): %v\n",
			metadataName, err)
	}

	dataUploader := dataTable.Uploader()
	metadataUploader := metadataTable.Uploader()

	step := 10000
	limit := len(data)
	for startIdx, endIdx := 0, step; startIdx < limit; startIdx, endIdx = startIdx+step, endIdx+step {
		if endIdx > limit {
			endIdx = limit
		}
		dataSlice := data[startIdx:endIdx]
		for err = dataUploader.Put(ctx.Context, dataSlice); err != nil; err = dataUploader.Put(ctx.Context, dataSlice) {
			log.Printf("Failed to write %d records to BigQuery table %s: %v\n",
				len(dataSlice), dataName, err)
			multiErr, ok := err.(bigquery.PutMultiError)
			if !ok {
				errs := append(errs, err)
				return metadataWritten, dataWritten, errs
			}
			log.Printf("Retrying data write to BigQuery table %s\n",
				dataName)
			newSlice := make([]interface{}, 0, len(multiErr))
			for _, rowInsertionErr := range multiErr {
				newSlice = append(newSlice,
					dataSlice[rowInsertionErr.RowIndex])
			}
			dataSlice = newSlice
		}
	}

	dataWritten = data

	if err := metadataUploader.Put(ctx.Context, metadata); err != nil {
		log.Printf("Error writing metadata to BigQuery table %s: %v\n",
			metadataName, err)
		errs = append(errs, err)
		return metadataWritten, dataWritten, errs
	}

	metadataWritten = metadata

	log.Printf("Wrote data to %s, %s BigQuery tables\n", dataName,
		metadataName)

	return metadataWritten, dataWritten, errs
}

// Load (test run, test results) pairs for given test runs. Use client in
// context to load data from bucket.
func LoadTestRunResults(ctx *GCSDatastoreContext, runs []base.TestRun) (
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

			keys := make([]base.TestRun, 0, len(progress))
			for key := range progress {
				keys = append(keys, key)
			}
			sort.Sort(metrics.ByCreatedDate(keys))

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

func processTestRun(ctx *GCSDatastoreContext, testRun *base.TestRun,
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
	prefixSliceStart := strings.Index(resultsURL, ctx.Bucket.Name) +
		len(ctx.Bucket.Name) + 1
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

func loadTestResults(ctx *GCSDatastoreContext, testRun *base.TestRun,
	objName string, resultChan chan metrics.TestRunResults,
	errChan chan error) {
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
