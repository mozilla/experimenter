#!/bin/bash

set -euo pipefail
set +x

TASKCLUSTER_API="https://firefox-ci-tc.services.mozilla.com/api/index/v1"
INDEX_BASE="mobile.v3.firefox-android.apks.fenix-beta.2024"
CURLFLAGS=("--proto" "=https" "--tlsv1.2" "-sS")

LATEST_BASE=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/namespaces/${INDEX_BASE}" | jq -r '.namespaces[-1].name' )

echo LATEST_BASE "${LATEST_BASE}"

LATEST_VERSION=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/namespaces/${INDEX_BASE}.${LATEST_BASE}" | jq -r '.namespaces[-1].name' )

echo LATEST_VERSION "${LATEST_VERSION}"

TASK_ID=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/tasks/${INDEX_BASE}.${LATEST_BASE}.${LATEST_VERSION}.latest" | jq -r '.tasks[-1].taskId')

echo TASK ID "${TASK_ID}"

echo "FIREFOX_FENIX_BUILD_ID=${TASK_ID}" > fenix-build.env
