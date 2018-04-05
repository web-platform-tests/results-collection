# Copyright 2017 The WPT Dashboard Project. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

SHELL := /bin/bash

all: lint test

.PHONY: lint
lint: .deps
	pycodestyle .

.PHONY: test
test: .deps
	python -m unittest discover -p '*_test.py' -s run

.deps: requirements.txt
	pip install -r requirements.txt
	touch .deps
