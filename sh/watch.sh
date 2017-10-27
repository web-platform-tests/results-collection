#!/bin/bash

set -e

SH_DIR=$(readlink -f $(dirname "$0"))
source "${SH_DIR}/logging.sh"

function stop() {
  warn "Recieved interrupt. Exiting..."
}

trap stop INT

PB_LIB=${PB_LIB:-"../protobuf/src"}
PROTOS=${PROTOS:-"./protos"}
BQ_LIB=${BQ_LIB:-"../protoc-gen-bq-schema"}
BQ_OUT=${BQ_OUT:-"./bq-schema"}
PY_OUT=${PY_OUT:-"./run/protos"}

mkdir -p "${BQ_OUT}"
mkdir -p "${PY_OUT}"

inotifywait -r -m -e close_write,moved_to,create,delete,modify "${PROTOS}" | \
    while read -r DIR EVTS F; do
      if [[ ${F} =~ [.]proto$ ]] && ! [[ ${F} =~ [#~] ]]; then
        if protoc -I"${PB_LIB}" -I"${BQ_LIB}" -I"${PROTOS}" \
          --bq-schema_out="${BQ_OUT}" \
          "${PROTOS}"/*.proto && \
          protoc -I"${PB_LIB}" -I"${BQ_LIB}" -I"${PROTOS}" \
          --python_out="${PY_OUT}" \
          "${BQ_LIB}"/*.proto "${PROTOS}"/*.proto; then
          info "SUCCESS: Regen from protos"
        else
          error "FAILURE: Regen from protos failed"
        fi
      else
        verbose "Non-proto file changed: ${DIR}${F}"
      fi
    done
