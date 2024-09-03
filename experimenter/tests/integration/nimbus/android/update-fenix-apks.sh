#!/bin/bash

set -euo pipefail
set +x

TASKCLUSTER_API="https://firefox-ci-tc.services.mozilla.com/api/index/v1"
INDEX_BASE="gecko.v2.mozilla-beta.latest.mobile"
CURLFLAGS=("--proto" "=https" "--tlsv1.2" "-sS")

TASK_ID=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/tasks/${INDEX_BASE}" | jq '.tasks[] | select(.namespace == "gecko.v2.mozilla-beta.latest.mobile.fenix-beta") | .taskId')

echo TASK ID "${TASK_ID}"

echo "FIREFOX_FENIX_TASK_ID=${TASK_ID}" > fenix-build.env

mv fenix-build.env ../../../
