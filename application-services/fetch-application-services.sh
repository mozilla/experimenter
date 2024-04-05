#!/bin/bash
#
# Fetch the megazords artifacts for Cirrus and Experimenter at the version
# specified in application-services.env

set -euo pipefail

TASKCLUSTER_HOST="https://firefox-ci-tc.services.mozilla.com"

function download_megazord {
    local PROJECT="${1}"
    local URL="${TASKCLUSTER_HOST}/api/index/v1/task/project.application-services.v2.${PROJECT}.${APPLICATION_SERVICES_BUILD_ID}/artifacts/public%2Fbuild%2F${PROJECT}.zip"

    echo download_megazord:
    echo PROJECT "${PROJECT}"
    echo URL "${URL}"

    curl --proto '=https' \
         --tlsv1.2 \
         -sSL \
         --output "${PROJECT}.zip" \
         "${URL}"

    unzip "${PROJECT}.zip" -d "/tmp/${PROJECT}"
}

function prepare_megazord {
    local PROJECT="${1}"
    local TARGET="${2}"
    local LIB_DIR="/tmp/${PROJECT}/${TARGET}"

    if [[ ! -d "${LIB_DIR}" ]]; then
        echo >&2 "Could not find libraries for target ${TARGET} at ${LIB_DIR}"
        exit 1
    fi

    mkdir -p "megazords/${PROJECT}"

    # Create a __init__.py so that the generated megazord behaves like a
    # package and allows for relative imports.
    touch "megazords/${PROJECT}/__init__.py"
    cp /tmp/"${PROJECT}"/*.py "megazords/${PROJECT}"
    cp /tmp/"${PROJECT}"/"${TARGET}"/* "megazords/${PROJECT}"

    rm -rf -- "/tmp/${PROJECT}"
}

source application-services.env
echo APPLICATION SERVICES VERSION "${APPLICATION_SERVICES_BUILD_ID}"

download_megazord cirrus
download_megazord nimbus-experimenter

TARGET=$(/tmp/cirrus/scripts/detect-target.sh)

if [[ -z "${TARGET}" ]]; then
    echo >&2 "Failed to detect target"
    exit 1
fi

echo TARGET "${TARGET}"

prepare_megazord cirrus "${TARGET}"
prepare_megazord nimbus-experimenter "${TARGET}"
