// Copyright 2017 The WPT Dashboard Project. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"sort"
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

/*


Collect metrics from WPT test runs

Runtime environment requirements:

  GCP Application Default Credentials
    Example of how to setup:
      $ gcloud config set project wptdashboard
      $ gcloud auth application-default login
      # ... follow prompts to authenticate in browser

Inputs:
  Latest WPT test runs exposed via WPTD endpoint

Outputs:
  - Compressed JSON files in GCS detailing metrics
  - BQ tables detailing metrics
  - Local logs in "current_metrics.log"

Run with:

  make go_deps && cd $GOPATH && go run \
    src/github.com/w3c/wptdashboard/metrics/run/collect_metrics.go [flags]

To run in development environment:

  make go_deps && cd $(go env GOPATH) && go run metrics/run/collect_metrics.go [flags]


Flags:

  wpt_data_path (default: $HOME/wpt-data)
    Path to data directory for local data copied from Google Cloud Storage

  project_id (default: wptdashboard)
    Google Cloud Platform project id

  input_gcs_bucket (default:
    Google Cloud Storage bucket where test results are stored

  output_gcs_bucket (default: wptd-metrics)
    Google Cloud Storage bucket where metrics are stored

  output_bq_metadata_dataset (default: wptd_metrics_[current UNIX time])
    BigQuery dataset where metrics metadata are stored

  output_bq_data_dataset (default: wptd_metrics_[current UNIX time])
    BigQuery dataset where metrics data are stored

  output_bq_pass_rate_table (default: PassRates_[current UNIX time])
    BigQuery table where pass rate metrics are stored

  output_bq_pass_rate_metadata_table (default: PassRateMetadata_[current UNIX time])
    BigQuery table where pass rate metrics are stored

  output_bq_failures_table (default: Failures_[current UNIX time])
    BigQuery table where test failure lists are stored

  output_bq_failures_metadata_table (default: FailuresMetadata_[current UNIX time])
    BigQuery table where pass rate metrics are stored

  wptd_host (default: wpt.fyi)
    Hostname of endpoint that serves WPT Dashboard data API

Data collection procedure:
  1. Fetch latest runs from WPTD endpoint
  2. Load each run's results by iterating over files in GCS folder associated
     with run's results
  3. Use raw run results as input to two metrics calculations:
     (a) Per directory/test file: Count of runs passing in [0, 1, ..., n]
         browsers
     (b) Per browser: tests failing in this browser and [0, 1, .., n - 1]
         browsers
  4. Upload metrics as JSON files to GCS and as tables to BQ

 */

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
	runs := base.FetchLatestRuns(*wptdHost)
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
	failuresMetrics := make(map[string][][]metrics.TestId)
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
			go func(browserName string, failuresMetric [][]metrics.TestId, outputter storage.Outputter) {
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

type FailureListsRow struct {
	BrowserName      string         `json:"browser_name"`
	NumOtherFailures int            `json:"num_other_failures"`
	Tests            metrics.TestId `json:"test"`
}
type ByTestId []interface{}

func (s ByTestId) Len() int          { return len(s) }
func (s ByTestId) Swap(i int, j int) { s[i], s[j] = s[j], s[i] }
func (s ByTestId) Less(i int, j int) bool {
	return s[i].(FailureListsRow).Tests.Test < s[j].(FailureListsRow).Tests.Test
}

func failureListsToRows(browserName string, failureLists [][]metrics.TestId) (
	rows []interface{}) {
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
				failure,
			})
		}
	}
	sort.Sort(ByTestId(rows))
	return rows
}

type PassRateMetricRow struct {
	Dir       string `json:"dir"`
	PassRates []int  `json:"pass_rates"`
	Total     int    `json:"total"`
}
type ByDir []interface{}

func (s ByDir) Len() int          { return len(s) }
func (s ByDir) Swap(i int, j int) { s[i], s[j] = s[j], s[i] }
func (s ByDir) Less(i int, j int) bool {
	return s[i].(PassRateMetricRow).Dir < s[j].(PassRateMetricRow).Dir
}

func totalsAndPassRateMetricToRows(totals map[string]int,
	passRateMetric map[string][]int) (
	rows []interface{}) {

	rows = make([]interface{}, 0, len(passRateMetric))
	for dir, passRates := range passRateMetric {
		rows = append(rows, PassRateMetricRow{dir, passRates,
			totals[dir]})
	}
	sort.Sort(ByDir(rows))
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
	browserName string, failureLists [][]metrics.TestId) (
	interface{}, []interface{}, []error) {
	rows := failureListsToRows(browserName, failureLists)
	return outputter.Output(id, metricsRun, rows)
}
