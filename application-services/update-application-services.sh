#!/bin/bash

set -euo pipefail
set +x

TASKCLUSTER_API="https://firefox-ci-tc.services.mozilla.com/api/index/v1"
INDEX_PREFIX="project.application-services.v2"
INDEX_BASE="${INDEX_PREFIX}.cirrus"
CURLFLAGS=("--proto" "=https" "--tlsv1.2" "-sS")

source megazords.env

function megazord_published {
    local MEGAZORD="${1}"
    local BUILD_ID="${2}"
    local URL="${TASKCLUSTER_API}/task/${INDEX_PREFIX}.${MEGAZORD}.${BUILD_ID}/artifacts/public%2Fbuild%2F${MEGAZORD}.zip"

    curl "${CURLFLAGS[@]}" -fL -r 0-0 -o /dev/null "${URL}"
}

LATEST_VERSION=$(curl "${CURLFLAGS[@]}" "${TASKCLUSTER_API}/namespaces/${INDEX_BASE}" | jq -r '[ .namespaces[].name | tonumber ] | max')

echo LATEST VERSION "${LATEST_VERSION}"

BUILD_IDS=$(curl "${CURLFLAGS[@]}" "${TASKCLUSTER_API}/tasks/${INDEX_BASE}.${LATEST_VERSION}" \
    | jq -r --arg prefix "${INDEX_BASE}." '[.tasks[].namespace | ltrimstr($prefix)] | sort | reverse | .[]')

for BUILD_ID in ${BUILD_IDS}; do
    UNPUBLISHED=""

    for MEGAZORD in ${MEGAZORDS}; do
        if ! megazord_published "${MEGAZORD}" "${BUILD_ID}"; then
            UNPUBLISHED="${MEGAZORD}"
            break
        fi
    done

    if [[ -n "${UNPUBLISHED}" ]]; then
        echo SKIPPING BUILD ID "${BUILD_ID}" - "${UNPUBLISHED}" megazord not published yet
        continue
    fi

    echo BUILD ID "${BUILD_ID}"

    echo "APPLICATION_SERVICES_BUILD_ID=${BUILD_ID}" > application-services.env
    exit 0
done

echo >&2 "No build of ${LATEST_VERSION} has all megazords published: ${MEGAZORDS}"
exit 1
