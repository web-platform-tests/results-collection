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
	python -m unittest discover -p '*_test.py'

.deps: requirements.txt
	pip install -r requirements.txt
	touch .deps

provisioning/infrastructure/.initialized:
	cd provisioning/infrastructure && terraform init

.PHONY: deploy
deploy: provisioning/infrastructure/.initialized
	cd provisioning/infrastructure && \
		terraform apply
	cd provisioning/configuration && \
		ansible-playbook \
			--inventory inventory/production \
			--limit 'all:!buildbot-macos-workers' \
			provision.yml

.PHONY: deploy-macos
deploy-macos:
	cd provisioning/configuration && \
		ansible-playbook \
			--inventory inventory/production \
			--ask-become-pass \
			--limit buildbot-macos-workers \
			provision.yml
