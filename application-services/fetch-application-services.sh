#!/bin/bash
#
# Fetch the megazords artifacts for Cirrus and Experimenter at the version
# specified in application-services.env
#
# A Python package is created for each megazord.

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
    local MEGAZORD="${PROJECT}/${PROJECT//-/_}_megazord"

    if [[ ! -d "${LIB_DIR}" ]]; then
        echo >&2 "Could not find libraries for target ${TARGET} at ${LIB_DIR}"
        exit 1
    fi

    mkdir -p "${MEGAZORD}"
    cp /tmp/"${PROJECT}"/*.py "${MEGAZORD}"
    cp /tmp/"${PROJECT}"/"${TARGET}"/* "${MEGAZORD}"

    # Adding __init__.py makes this into a Python package.
    echo "" > "${MEGAZORD}/__init__.py"

    rm -rf -- "/tmp/${PROJECT}"
    rm -- "${PROJECT}.zip"
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
