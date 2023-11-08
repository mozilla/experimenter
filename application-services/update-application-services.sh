#!/bin/bash

set -euo pipefail
set +x

TASKCLUSTER_API="https://firefox-ci-tc.services.mozilla.com/api/index/v1"
INDEX_BASE="project.application-services.v2.cirrus"
CURLFLAGS=("--proto" "=https" "--tlsv1.2" "-sS")

LATEST_VERSION=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/namespaces/${INDEX_BASE}" | jq -r '[ .namespaces[].name | tonumber ] | max')

echo LATEST VERSION "${LATEST_VERSION}"

INDEX=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/tasks/${INDEX_BASE}.${LATEST_VERSION}" | jq -r '[.tasks[].namespace] | max')

echo INDEX "${INDEX}"

BUILD_ID="${INDEX#"${INDEX_BASE}."}"

echo BUILD ID "${BUILD_ID}"

echo "APPLICATION_SERVICES_BUILD_ID=${BUILD_ID}" > application-services.env
