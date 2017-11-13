# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Make targets in this file are intended to be run inside the Docker container
# environment.

# Make targets can be run in a host environment, but that requires ensuring
# the correct version of tools are installed and environment variables are
# set appropriately.

WPTD_PATH ?= /home/jenkins/wptdashboard

PB_LIB_DIR ?= ../protobuf/src
PB_BQ_LIB_DIR ?= ../protoc-gen-bq-schema
PB_LOCAL_LIB_DIR ?= protos
PB_BQ_OUT_DIR ?= bq-schema
PB_PY_OUT_DIR ?= run/protos

PROTOS=$(wildcard $(PB_LOCAL_LIB_DIR)/*.proto)

build: go_deps proto

test: py_test go_test

# Note: Do not depend on jenkins_install; it should run as root
jenkins_test: proto
	$(WPTD_PATH)/util/docker-jenkins/inner/travis_ci_run.sh

jenkins_install: py_deps
	$(WPTD_PATH)/util/docker-jenkins/inner/travis_ci_install.sh

lint: py_lint go_lint

proto: bq_proto py_proto

py_lint: py_proto py_deps
	pycodestyle --exclude=*_pb2.py .

py_test: py_proto py_deps
	python -m unittest discover -p '*_test.py'

go_lint: go_deps
	golint -set_exit_status

go_test: go_deps
	go test -v ./...

bq_proto: $(PROTOS)
	mkdir -p $(PB_BQ_OUT_DIR)
	protoc -I$(PB_LIB_DIR) -I$(PB_BQ_LIB_DIR) -I$(PB_LOCAL_LIB_DIR) \
		--bq-schema_out=$(PB_BQ_OUT_DIR) $(PROTOS)

py_proto: $(PROTOS)
	mkdir -p $(PB_PY_OUT_DIR)
	protoc -I$(PB_LIB_DIR) -I$(PB_BQ_LIB_DIR) -I$(PB_LOCAL_LIB_DIR) \
		--python_out=$(PB_PY_OUT_DIR) $(PROTOS)

py_deps: $(find . -type f | grep '\.py$' | grep -v '\_pb.py$')
	pip install -r requirements.txt

go_deps: $(find .  -type f | grep '\.go$' | grep -v '\.pb.go$')
	cd $(GOPATH)/src/wptdashboard; go get -t ./...
