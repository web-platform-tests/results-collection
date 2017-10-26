#!/bin/bash

set -e

WATCH_DIR=${WATCH_DIR:-"."}
PB_LIB=${PB_LIB:-"../protobuf/src"}
PROTOS=${PROTOS:-"./protos"}
BQ_LIB=${BQ_LIB:-"../protoc-gen-bq-schema"}
BQ_OUT=${BQ_OUT:-"./bq-schema"}
PY_OUT=${PY_OUT:-"./run/protos"}

mkdir -p "${BQ_OUT}"
mkdir -p "${PY_OUT}"

inotifywait -r -m -e close_write,moved_to,create,delete "${WATCH_DIR}" |
  while read -r dir evts f; do
    if [[ ${f} =~ [.]proto$ ]] && ! [[ ${f} =~ [#~] ]]; then
      echo "[ INFO ] Proto file changed: ${dir}${f}"
      if protoc -I"${PB_LIB}" -I"${BQ_LIB}" -I"${PROTOS}" \
        --bq-schema_out="${BQ_OUT}" \
        "${PROTOS}"/*.proto && \
        protoc -I"${PB_LIB}" -I"${BQ_LIB}" -I"${PROTOS}" \
        --python_out="${PY_OUT}" \
        "${BQ_LIB}"/*.proto "${PROTOS}"/*.proto; then
        echo "[ INFO ] Regen from protos"
      else
        echo "[ ERRR ] Regen from protos failed"
      fi
    else
      echo "[ VERB ] Non-proto file changed: ${dir}${f}"
    fi
  done
