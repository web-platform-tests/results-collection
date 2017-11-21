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
WPTD_PATH="${DOCKER_INNER_DIR}/../../.."

function stop() {
  warn "watch.sh: Recieved interrupt. Exiting..."
}

trap stop INT

PB_LIB=${PB_LIB:-"/protobuf/src"}
PROTOS=${PROTOS:-"./protos"}
BQ_LIB=${BQ_LIB:-"/protoc-gen-bq-schema"}

function compile_protos() {
  pushd "${WPTD_PATH}" > /dev/null
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
