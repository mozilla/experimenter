#!/bin/bash

set -euo pipefail
set +x

TASKCLUSTER_API="https://firefox-ci-tc.services.mozilla.com/api/index/v1"
WHAT_TRAIN_IS_IT_NOW_API="https://whattrainisitnow.com/api/firefox/releases/"
CURLFLAGS=("--proto" "=https" "--tlsv1.2" "-sS")

if [ $# -eq 0 ]; then
    echo "No arguments provided. Please provide an argument."
    exit 1
fi

input="$1"

case $input in
    fenix-beta)
        INDEX_BASE="mobile.v3.firefox-android.apks.fenix-beta.latest"
        TASK_ID=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/tasks/${INDEX_BASE}" | jq '.tasks[] | select(.namespace == "mobile.v3.firefox-android.apks.fenix-beta.latest.x86_64") | .taskId')
        echo FIREFOX_FENIX_BETA_TASK_ID TASK ID "${TASK_ID}"
        echo "FIREFOX_FENIX_BETA_TASK_ID=${TASK_ID}" > firefox-fenix-beta-build.env
        mv firefox-fenix-beta-build.env experimenter/tests
        ;;
    fenix-nightly)
        INDEX_BASE="mobile.v3.firefox-android.apks.fenix-nightly.latest"
        TASK_ID=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/tasks/${INDEX_BASE}" | jq '.tasks[] | select(.namespace == "mobile.v3.firefox-android.apks.fenix-nightly.latest.x86_64") | .taskId')
        echo FIREFOX_FENIX_NIGHTLY_TASK_ID TASK ID "${TASK_ID}"
        echo "FIREFOX_FENIX_NIGHTLY_TASK_ID=${TASK_ID}" > firefox-fenix-nightly-build.env
        mv firefox-fenix-nightly-build.env experimenter/tests
        ;;
    desktop-beta)
        INDEX_BASE="gecko.v2.mozilla-beta.latest.firefox"
        TASK_ID=$(curl ${CURLFLAGS[@]} "${TASKCLUSTER_API}/tasks/${INDEX_BASE}" | jq '.tasks[] | select(.namespace == "gecko.v2.mozilla-beta.latest.firefox.linux64-debug") | .taskId')
        echo FIREFOX_BETA_TASK_ID "${TASK_ID}"
        echo "FIREFOX_BETA_TASK_ID=${TASK_ID}" > firefox-desktop-beta-build.env
        mv firefox-desktop-beta-build.env experimenter/tests
        ;;
    desktop-release)
        RELEASE_VERSION=$(curl ${CURLFLAGS[@]} "${WHAT_TRAIN_IS_IT_NOW_API}" | jq 'to_entries | last | .key')
        echo FIREFOX_RELEASE_VERSION_ID "${RELEASE_VERSION}"
        echo "FIREFOX_RELEASE_VERSION_ID=${RELEASE_VERSION}" > firefox-desktop-release-build.env
        mv firefox-desktop-release-build.env experimenter/tests
        ;;
    *)
        echo "Invalid option."
        ;;
esac
