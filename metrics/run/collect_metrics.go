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

	"cloud.google.com/go/bigquery"
	"cloud.google.com/go/datastore"
	gcs "cloud.google.com/go/storage"
	"github.com/w3c/wptdashboard/metrics"
	"github.com/w3c/wptdashboard/metrics/compute"
	"github.com/w3c/wptdashboard/metrics/storage"
	base "github.com/w3c/wptdashboard/shared"
	"golang.org/x/net/context"
)

var wptDataPath *string
var projectId *string
var inputGcsBucket *string
var outputGcsBucket *string
var wptdHost *string
var outputBQMetadataDataset *string
var outputBQDataDataset *string
var outputBQPassRateTable *string
var outputBQPassRateMetadataTable *string
var outputBQFailuresTable *string
var outputBQFailuresMetadataTable *string

func init() {
	unixNow := time.Now().Unix()
	wptDataPath = flag.String("wpt_data_path", os.Getenv("HOME")+
		"/wpt-data", "Path to data directory for local data copied "+
		"from Google Cloud Storage")
	projectId = flag.String("project_id", "wptdashboard",
		"Google Cloud Platform project id")
	inputGcsBucket = flag.String("input_gcs_bucket", "wptd",
		"Google Cloud Storage bucket where test results are stored")
	outputGcsBucket = flag.String("output_gcs_bucket", "wptd-metrics",
		"Google Cloud Storage bucket where metrics are stored")
	outputBQMetadataDataset = flag.String("output_bq_metadata_dataset",
		fmt.Sprintf("wptd_metrics_%d", unixNow),
		"BigQuery dataset where metrics metadata are stored")
	outputBQDataDataset = flag.String("output_bq_data_dataset",
		fmt.Sprintf("wptd_metrics_%d", unixNow),
		"BigQuery dataset where metrics data are stored")
	outputBQPassRateTable = flag.String("output_bq_pass_rate_table",
		fmt.Sprintf("PassRates_%d", unixNow),
		"BigQuery table where pass rate metrics are stored")
	outputBQPassRateMetadataTable = flag.String("output_bq_pass_rate_metadata_table",
		fmt.Sprintf("PassRateMetadata_%d", unixNow),
		"BigQuery table where pass rate metrics are stored")
	outputBQFailuresTable = flag.String("output_bq_failures_table",
		fmt.Sprintf("Failures_%d", unixNow),
		"BigQuery table where test failure lists are stored")
	outputBQFailuresMetadataTable = flag.String("output_bq_failures_metadata_table",
		fmt.Sprintf("FailuresMetadata_%d", unixNow),
		"BigQuery table where pass rate metrics are stored")
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
	inputCtx := storage.GCSDatastoreContext{
		Context: ctx,
		Bucket: storage.Bucket{
			Name:   *inputGcsBucket,
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
			&resultsById, compute.OkAndUnknownOrPasses)
	}()
	for _, run := range runs {
		go func(browserName string) {
			defer wg.Done()
			// TODO: Check that browser names are different
			failuresMetrics[browserName] =
				compute.ComputeBrowserFailureList(len(runs),
					browserName, &resultsById,
					compute.OkAndUnknownOrPasses)
		}(run.BrowserName)
	}
	wg.Wait()

	log.Println("Computed metrics")
	log.Println("Uploading metrics")

	outputBucket := gcsClient.Bucket(*outputGcsBucket)
	datastoreClient, err := datastore.NewClient(ctx, *projectId)
	if err != nil {
		log.Fatal(err)
	}
	bigqueryClient, err := bigquery.NewClient(ctx, *projectId)
	if err != nil {
		log.Fatal(err)
	}
	outputters := [2]storage.Outputter{
		storage.GCSDatastoreContext{
			Context: ctx,
			Bucket: storage.Bucket{
				Name:   *outputGcsBucket,
				Handle: outputBucket,
			},
			Client: datastoreClient,
		},
		storage.BQContext{
			Context: ctx,
			Client:  bigqueryClient,
		},
	}

	gcsDir := fmt.Sprintf("%d-%d", readStartTime.Unix(),
		readEndTime.Unix())
	passRatesBasename := "pass-rates"
	passRateGCSPath := fmt.Sprintf("%s/%s.json.gz", gcsDir,
		passRatesBasename)
	passRatesUrl := fmt.Sprintf(
		"https://storage.googleapis.com/%s/%s",
		*outputGcsBucket,
		passRateGCSPath)
	failuresBasenamef := func(browserName string) string {
		return fmt.Sprintf("%s-failures", browserName)
	}
	failuresGCSPathf := func(browserName string) string {
		return fmt.Sprintf("%s/%s.json.gz", gcsDir,
			failuresBasenamef(browserName))
	}
	failuresUrlf := func(browserName string) string {
		return fmt.Sprintf(
			"https://storage.googleapis.com/%s/%s",
			*outputGcsBucket,
			failuresGCSPathf(browserName))
	}
	passRateMetadata := metrics.PassRateMetadata{
		StartTime: readStartTime,
		EndTime:   readEndTime,
		TestRuns:  runs,
		DataUrl:   passRatesUrl,
	}

	wg.Add((1 + len(failuresMetrics)) * len(outputters))
	processUploadErrors := func(errs []error) {
		for _, err := range errs {
			log.Printf("Upload error: %v", err)
		}
		if len(errs) > 0 {
			log.Fatal(errs[len(errs)-1])
		}
	}
	for _, outputter := range outputters {
		go func(outputter storage.Outputter) {
			defer wg.Done()
			outputId := storage.OutputId{
				MetadataLocation: storage.OutputLocation{
					BQDatasetName: *outputBQMetadataDataset,
					BQTableName:   *outputBQPassRateMetadataTable,
				},
				DataLocation: storage.OutputLocation{
					GCSObjectPath: passRateGCSPath,
					BQDatasetName: *outputBQDataDataset,
					BQTableName:   *outputBQPassRateTable,
				},
			}
			_, _, errs := uploadTotalsAndPassRateMetric(
				&passRateMetadata, outputter, outputId, totals,
				passRateMetric)
			processUploadErrors(errs)
		}(outputter)
		for browserName, failuresMetric := range failuresMetrics {
			go func(browserName string, failuresMetric [][]*metrics.TestId, outputter storage.Outputter) {
				defer wg.Done()
				failuresMetadata := metrics.FailuresMetadata{
					StartTime:   readStartTime,
					EndTime:     readEndTime,
					TestRuns:    runs,
					DataUrl:     failuresUrlf(browserName),
					BrowserName: browserName,
				}
				outputId := storage.OutputId{
					MetadataLocation: storage.OutputLocation{
						BQDatasetName: *outputBQMetadataDataset,
						BQTableName:   *outputBQFailuresMetadataTable,
					},
					DataLocation: storage.OutputLocation{
						GCSObjectPath: gcsDir +
							"/" +
							failuresBasenamef(browserName) +
							".json.gz",
						BQDatasetName: *outputBQDataDataset,
						BQTableName:   *outputBQFailuresTable,
					},
				}
				_, _, errs := uploadFailureLists(&failuresMetadata,
					outputter, outputId, browserName,
					failuresMetric)
				processUploadErrors(errs)
			}(browserName, failuresMetric, outputter)
		}
	}
	wg.Wait()

	log.Printf("Uploaded metrics")
}

func getRuns() []base.TestRun {
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
	var runs []base.TestRun
	if err := json.Unmarshal(body, &runs); err != nil {
		log.Fatal(err)
	}
	return runs
}

func failureListsToRows(browserName string, failureLists [][]*metrics.TestId) (
	rows []interface{}) {
	type FailureListsRow struct {
		BrowserName      string         `json:"browser_name"`
		NumOtherFailures int            `json:"num_other_failures"`
		Tests            metrics.TestId `json:"test"`
	}
	numRows := 0
	for _, failureList := range failureLists {
		numRows += len(failureList)
	}
	rows = make([]interface{}, 0, numRows)
	for i, failuresPtrList := range failureLists {
		for _, failure := range failuresPtrList {
			rows = append(rows, FailureListsRow{
				browserName,
				i,
				*failure,
			})
		}
	}
	return rows
}

func totalsAndPassRateMetricToRows(totals map[string]int,
	passRateMetric map[string][]int) (
	rows []interface{}) {
	type PassRateMetricRow struct {
		Dir       string `json:"dir"`
		PassRates []int  `json:"pass_rates"`
		Total     int    `json:"total"`
	}
	rows = make([]interface{}, 0, len(passRateMetric))
	for dir, passRates := range passRateMetric {
		rows = append(rows, PassRateMetricRow{dir, passRates,
			totals[dir]})
	}
	return rows
}

func uploadTotalsAndPassRateMetric(metricsRun *metrics.PassRateMetadata,
	outputter storage.Outputter, id storage.OutputId,
	totals map[string]int, passRateMetric map[string][]int) (
	interface{}, []interface{}, []error) {
	rows := totalsAndPassRateMetricToRows(totals, passRateMetric)
	return outputter.Output(id, metricsRun, rows)
}

func uploadFailureLists(metricsRun *metrics.FailuresMetadata,
	outputter storage.Outputter, id storage.OutputId,
	browserName string, failureLists [][]*metrics.TestId) (
	interface{}, []interface{}, []error) {
	rows := failureListsToRows(browserName, failureLists)
	return outputter.Output(id, metricsRun, rows)
}
