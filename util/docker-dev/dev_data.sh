#!/usr/bin/env bash

DOCKER_DIR=$(dirname "$0")
source "${DOCKER_DIR}/../logging.sh"

# Run util/populate_dev_data.go (via make) in the docker environment.

# This script copies the file found under the $GOOGLE_APPLICATION_CREDENTIALS
# environment variable across to the docker instance, and sets the instance's
# same environment variable to point to the copy.

DOCKER_INSTANCE=wptd-dev-instance
DEFAULT_CREDS_FILE=/home/application_default_credentials.json
COPY_COMMAND="docker cp ${GOOGLE_APPLICATION_CREDENTIALS} ${DOCKER_INSTANCE}:${DEFAULT_CREDS_FILE}"
ENVIRONMENT_VAR="-e GOOGLE_APPLICATION_CREDENTIALS=${DEFAULT_CREDS_FILE}"

if [[ "${GOOGLE_APPLICATION_CREDENTIALS}" == "" ]]
then
    warn "Environment variable \$GOOGLE_APPLICATION_CREDENTIALS not set."
    warn "See https://developers.google.com/accounts/docs/application-default-credentials for more information."
    ENVIRONMENT_VAR=""
else
    info "${COPY_COMMAND}"
    ${COPY_COMMAND}
fi

docker exec -t -u $(id -u $USER):$(id -g $USER) ${ENVIRONMENT_VAR} ${DOCKER_INSTANCE} make dev_data
