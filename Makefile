# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Make targets in this file are intended to be run inside the Docker container
# environment.

# Make targets can be run in a host environment, but that requires ensuring
# the correct version of tools are installed and environment variables are
# set appropriately.

SHELL := /bin/bash

WPTD_PATH ?= /home/jenkins/wptdashboard
WPTD_GO_PATH ?= $(GOPATH)/src/github.com/w3c/wptdashboard

PB_LIB_DIR ?= ../protobuf/src
PB_BQ_LIB_DIR ?= ../protoc-gen-bq-schema
PB_LOCAL_LIB_DIR ?= protos
PB_BQ_OUT_DIR ?= bq-schema
PB_PY_OUT_DIR ?= run/protos
PB_GO_OUT_DIR ?= generated
PB_GO_PKG_MAP ?= Mbq_table_name.proto=github.com/GoogleCloudPlatform/protoc-gen-bq-schema/protos

PROTOS=$(wildcard $(PB_LOCAL_LIB_DIR)/*.proto)

build: go_deps proto

test: py_test go_test

# Note: Do not depend on jenkins_install; it should run as root
jenkins_test: proto
	$(WPTD_PATH)/util/docker-jenkins/inner/travis_ci_run.sh

jenkins_install: py_deps
	$(WPTD_PATH)/util/docker-jenkins/inner/travis_ci_install.sh

lint: py_lint go_lint

proto: bq_proto go_proto py_proto

py_lint: py_proto py_deps
	pycodestyle --exclude=*_pb2.py .

py_test: py_proto py_deps
	python -m unittest discover -p '*_test.py'

go_lint: go_deps
	cd $(WPTD_GO_PATH); golint -set_exit_status
	# Print differences between current/gofmt'd output, check empty.
	cd $(WPTD_GO_PATH); ! gofmt -d . 2>&1 | read

go_test: go_deps
	cd $(WPTD_GO_PATH); go test -v ./...

bq_proto: $(PROTOS)
	mkdir -p $(PB_BQ_OUT_DIR)
	protoc -I$(PB_LIB_DIR) -I$(PB_BQ_LIB_DIR) -I$(PB_LOCAL_LIB_DIR) \
		--bq-schema_out=$(PB_BQ_OUT_DIR) $(PROTOS)

go_proto: $(PROTOS)
	mkdir -p $(PB_GO_OUT_DIR)
	protoc -I$(PB_LIB_DIR) -I$(PB_BQ_LIB_DIR) -I$(PB_LOCAL_LIB_DIR) \
		--go_out=$(PB_GO_PKG_MAP):$(PB_GO_OUT_DIR) $(PROTOS)

py_proto: $(PROTOS)
	mkdir -p $(PB_PY_OUT_DIR)
	protoc -I$(PB_LIB_DIR) -I$(PB_BQ_LIB_DIR) -I$(PB_LOCAL_LIB_DIR) \
		--python_out=$(PB_PY_OUT_DIR) $(PROTOS)

py_deps: $(find . -type f | grep '\.py$' | grep -v '\_pb.py$')
	pip install -r requirements.txt

go_deps: $(find .  -type f | grep '\.go$' | grep -v '\.pb.go$')
	cd $(WPTD_GO_PATH); go get -t ./...
