: '
An end-to-end test of both local configurations (Chrome, FF),
and remote (Edge, Safari).

This script must pass in order for an image to be pushed
to production for test runners to pull.
'
BASE_IMAGE_NAME="wptd-base"
JENKINS_IMAGE_NAME="wptd-testrun-jenkins"
JENKINS_DOCKERFILE="Dockerfile.jenkins"

docker build -t "${BASE_IMAGE_NAME}" .
docker build -t "${JENKINS_IMAGE_NAME}" -f "${JENKINS_DOCKERFILE}" .

docker run \
  -p 4445:4445 \
  --entrypoint "/bin/bash" "${JENKINS_IMAGE_NAME}" \
  /wptdashboard/util/jenkins_container_inner.sh
