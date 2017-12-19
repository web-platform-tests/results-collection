// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"

	gcs "cloud.google.com/go/storage"
	"github.com/w3c/wptdashboard/metrics"
	"github.com/w3c/wptdashboard/metrics/compute"
	"github.com/w3c/wptdashboard/metrics/storage"
	"golang.org/x/net/context"
)

var wptDataPath *string
var projectId *string
var inputGcsBucket *string
var outputGcsBucket *string
var wptdHost *string

func getRuns() metrics.TestRunSlice {
	url := "https://" + *wptdHost + "/api/runs"
	resp, err := http.Get(url)
	if err != nil {
		log.Fatal(err)
	}
	if resp.StatusCode != 200 {
		log.Fatal(errors.New("Bad response code from " + url + ": " +
			strconv.Itoa(resp.StatusCode)))
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}
	var runs metrics.TestRunSlice
	if err := json.Unmarshal(body, &runs); err != nil {
		log.Fatal(err)
	}
	return runs
}

func init() {
	wptDataPath = flag.String("wpt_data_path", os.Getenv("HOME")+
		"/wpt-data", "Path to data directory for local data copied "+
		"from Google Cloud Storage")
	projectId = flag.String("project_id", "wptdashboard",
		"Google Cloud Platform project id")
	inputGcsBucket = flag.String("input_gcs_bucket", "wptd",
		"Google Cloud Storage bucket where test results are stored")
	outputGcsBucket = flag.String("output_gcs_bucket", "wptd-metrics",
		"Google Cloud Storage bucket where metrics are stored")
	wptdHost = flag.String("wptd_host", "wpt.fyi",
		"Hostname of endpoint that serves WPT Dashboard data API")
}

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)

	logFileName := "current_metrics.log"
	logFile, err := os.OpenFile(logFileName, os.O_RDWR|os.O_CREATE|
		os.O_APPEND, 0666)
	if err != nil {
		log.Fatalf("Error opening log file: %v", err)
	}
	defer logFile.Close()
	log.Printf("Logs appended to %s\n", logFileName)
	log.SetOutput(logFile)

	ctx := context.Background()
	gcsClient, err := gcs.NewClient(ctx)
	if err != nil {
		log.Fatal(err)
	}
	inputBucket := gcsClient.Bucket(*inputGcsBucket)
	inputCtx := storage.Context{
		Context: ctx,
		Client:  gcsClient,
		Bucket: &storage.Bucket{
			Name:   inputGcsBucket,
			Handle: inputBucket,
		},
	}

	log.Println("Reading test results from Google Cloud Storage bucket: " +
		*inputGcsBucket)

	readStartTime := time.Now()
	runs := getRuns()
	allResults := storage.LoadTestRunResults(&inputCtx, runs)
	readEndTime := time.Now()

	log.Println("Read test results from Google Cloud Storage bucket: " +
		*inputGcsBucket)
	log.Println("Consolidating results")

	resultsById := compute.GatherResultsById(&allResults)

	log.Println("Consolidated results")
	log.Println("Computing metrics")

	var totals map[string]int
	var passRateMetric map[string][]int
	failuresMetrics := make(map[string][][]*metrics.TestId)
	var wg sync.WaitGroup
	wg.Add(2 + len(runs))
	go func() {
		defer wg.Done()
		totals = compute.ComputeTotals(&resultsById)
	}()
	go func() {
		defer wg.Done()
		passRateMetric = compute.ComputePassRateMetric(len(runs),
			&resultsById, compute.OkAndUnknonwOrPasses)
	}()
	for _, run := range runs {
		go func(browserName string) {
			defer wg.Done()
			// TODO: Check that browser names are different
			failuresMetrics[browserName] =
				compute.ComputeBrowserFailureList(len(runs),
					browserName, &resultsById,
					compute.OkAndUnknonwOrPasses)
		}(run.BrowserName)
	}
	wg.Wait()

	log.Println("Computed metrics")
	log.Printf("Writing metrics to Google Cloud Storage bucket: %s\n",
		*outputGcsBucket)

	outputBucket := gcsClient.Bucket(*outputGcsBucket)
	outputCtx := storage.Context{
		Context: ctx,
		Client:  gcsClient,
		Bucket: &storage.Bucket{
			Name:   outputGcsBucket,
			Handle: outputBucket,
		},
	}
	metricsRun := metrics.MetricsRun{
		StartTime: &readStartTime,
		EndTime:   &readEndTime,
		TestRuns:  &runs,
	}

	outputDir := fmt.Sprintf("%d-%d", metricsRun.StartTime.Unix(),
		metricsRun.EndTime.Unix())
	outputErrs := make(chan error)
	log.Printf("Writing to bucket directory %s\n", outputDir)
	wg.Add(2 + len(failuresMetrics))
	go func() {
		defer wg.Done()
		objName := fmt.Sprintf("%s/pass-rates.json.gz", outputDir)
		passRateSummary := metrics.MetricsRunData{
			MetricsRun: &metricsRun,
			Data:       &passRateMetric,
		}
		err := storage.UploadMetricsRunData(&outputCtx, &objName,
			&passRateSummary)
		if err != nil {
			log.Println(err)
			outputErrs <- err
		}
	}()
	go func() {
		defer wg.Done()
		objName := fmt.Sprintf("%d-%d/test-counts.json.gz",
			metricsRun.StartTime.Unix(),
			metricsRun.EndTime.Unix())
		totalsSummary := metrics.MetricsRunData{
			MetricsRun: &metricsRun,
			Data:       &totals,
		}
		err := storage.UploadMetricsRunData(&outputCtx, &objName,
			&totalsSummary)
		if err != nil {
			log.Println(err)
			outputErrs <- err
		}
	}()
	for browserName, values := range failuresMetrics {
		go func(browserName string, values [][]*metrics.TestId) {
			defer wg.Done()
			objName := fmt.Sprintf("%d-%d/failures-%s.json.gz",
				metricsRun.StartTime.Unix(),
				metricsRun.EndTime.Unix(),
				browserName)
			failureSummary := metrics.MetricsRunData{
				MetricsRun: &metricsRun,
				Data:       &values,
			}
			err := storage.UploadMetricsRunData(&outputCtx,
				&objName, &failureSummary)
			if err != nil {
				log.Println(err)
				outputErrs <- err
			}
		}(browserName, values)
	}
	wg.Wait()

	close(outputErrs)
	outputErrsSlice := make([]error, 0)
	for err := range outputErrs {
		outputErrsSlice = append(outputErrsSlice, err)
	}
	if len(outputErrsSlice) > 0 {
		log.Fatal(outputErrsSlice)
	}

	log.Printf("Wrote metrics to Google Cloud Storage bucket: %s\n",
		*outputGcsBucket)
}
