: '
An end-to-end test of both local configurations (Chrome, FF),
and remote (Edge, Safari).

This script must pass in order for an image to be pushed
to production for test runners to pull.
'
IMAGE_NAME=wptd-testrun-jenkins

docker build -t "${IMAGE_NAME}" .

docker run \
  -p 4445:4445 \
  --entrypoint "/bin/bash" "${IMAGE_NAME}" \
  /wptdashboard/util/ci_container_inner.sh
