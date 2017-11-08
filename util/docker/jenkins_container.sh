: '
An end-to-end test of both local configurations (Chrome, FF),
and remote (Edge, Safari).

This script must pass in order for an image to be pushed
to production for test runners to pull.
'
DOCKER_DIR=$(dirname "$0")
WPTDASHBOARD_DIR=${WPTDASHBOARD_DIR:-"${DOCKER_DIR}/../.."}
BASE_IMAGE_NAME="wptd-base"
JENKINS_IMAGE_NAME="wptd-testrun-jenkins"
JENKINS_DOCKERFILE="${WPTDASHBOARD_DIR}/Dockerfile.jenkins"

docker build -t "${BASE_IMAGE_NAME}" "${WPTDASHBOARD_DIR}"
docker build -t "${JENKINS_IMAGE_NAME}" -f "${JENKINS_DOCKERFILE}" "${WPTDASHBOARD_DIR}"

docker run \
  -p 4445:4445 \
  --entrypoint "/bin/bash" "${JENKINS_IMAGE_NAME}" \
  /wptdashboard/util/docker/inner/jenkins_run.sh
