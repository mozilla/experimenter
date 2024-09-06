#!/bin/bash

set -euo pipefail
set +x

TASKCLUSTER_API="https://firefox-ci-tc.services.mozilla.com/api/index/v1"
CURLFLAGS=("--proto" "=https" "--tlsv1.2" "-sS")

if [ $# -eq 0 ]; then
    echo "No arguments provided. Please provide an argument."
    exit 1
fi

input="$1"

case $input in
    fenix)
        INDEX_BASE="gecko.v2.mozilla-beta.latest.mobile"
        TASK_ID=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/tasks/${INDEX_BASE}" | jq '.tasks[] | select(.namespace == "gecko.v2.mozilla-beta.latest.mobile.fenix-beta") | .taskId')
        echo TASK ID "${TASK_ID}"
        echo "FIREFOX_FENIX_TASK_ID=${TASK_ID}" > firefox-fenix-build.env
        mv firefox-fenix-build.env experimenter/tests
        ;;
    desktop-beta)
        INDEX_BASE="gecko.v2.mozilla-beta.latest.firefox"
        TASK_ID=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/tasks/${INDEX_BASE}" | jq '.tasks[] | select(.namespace == "gecko.v2.mozilla-beta.latest.firefox.linux-debug") | .taskId')
        echo TASK ID "${TASK_ID}"
        echo "FIREFOX_BETA_TASK_ID=${TASK_ID}" > firefox-desktop-beta-build.env
        mv firefox-desktop-beta-build.env experimenter/tests
        ;;
    *)
        echo "Invalid option."
        ;;
esac
