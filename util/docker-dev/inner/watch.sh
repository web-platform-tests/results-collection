#!/bin/bash

#
# File-watching development server script that run inside Docker development
# image.
#
# Presumed working directory in Docker instance is "/wptdashboard" mapped to
# source repository root directory.
#

set -e

DOCKER_INNER_DIR=$(dirname "$0")
source "${DOCKER_INNER_DIR}/../../logging.sh"
WPTDASHBOARD_DIR="${DOCKER_INNER_DIR}/../../.."

function stop() {
  warn "watch.sh: Recieved interrupt. Exiting..."
}

trap stop INT

PB_LIB=${PB_LIB:-"../protobuf/src"}
PROTOS=${PROTOS:-"./protos"}
BQ_LIB=${BQ_LIB:-"../protoc-gen-bq-schema"}
BQ_OUT=${BQ_OUT:-"./bq-schema"}
PY_OUT=${PY_OUT:-"./run/protos"}

mkdir -p "${BQ_OUT}"
mkdir -p "${PY_OUT}"

function compile_protos() {
  pushd "${WPTDASHBOARD_DIR}" > /dev/null
  if make proto; then
    info "SUCCESS: Regen from protos"
  else
    error "FAILURE: Regen from protos failed"
  fi
  popd > /dev/null
}

compile_protos

inotifywait -r -m -e close_write,moved_to,create,delete,modify "${PROTOS}" | \
    while read -r DIR EVTS F; do
      if [[ ${F} =~ [.]proto$ ]] && ! [[ ${F} =~ [#~] ]]; then
        compile_protos
      else
        verbose "Non-proto file changed: ${DIR}${F}"
      fi
    done
