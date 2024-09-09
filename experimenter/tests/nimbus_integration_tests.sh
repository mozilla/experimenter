#!/bin/bash

set -euo pipefail
set +x

export PATH=$PATH:/home/seluser/.local/bin

PYTEST_ARGS=${PYTEST_ARGS:-"-k FIREFOX_DESKTOP"}

if [[ -n "${UPDATE_FIREFOX_VERSION}" ]]; then
    sudo ./experimenter/tests/integration/nimbus/utils/nightly-install.sh
fi

if [[ -n "${FIREFOX_BETA}" ]]; then
    source ./experimenter/tests/firefox-desktop-beta-build.env
    FIREFOX_BETA_TASK_ID=${FIREFOX_BETA_TASK_ID//\"/}
    echo "Installing firefox beta from taskcluster"
    sudo apt-get update -qqy
    sudo rm -rf /var/lib/apt/lists/* /var/cache/apt/*
    sudo wget --no-verbose -O /tmp/firefox.tar.bz2 "https://firefox-ci-tc.services.mozilla.com/api/queue/v1/task/${FIREFOX_BETA_TASK_ID}/artifacts/public/build/target.tar.bz2"
    sudo rm -rf /opt/firefox-latest
    sudo tar -C /opt -xjf /tmp/firefox.tar.bz2
    sudo rm /tmp/firefox.tar.bz2
    sudo ln -fs /opt/firefox/firefox /usr/bin/firefox
    sudo chown -R seluser /opt/firefox/firefox
fi

curl -sSL https://install.python-poetry.org | python3 - --version 1.8.3
sudo chmod -R a+rwx /code/experimenter/tests/integration/
mkdir -m a+rwx /code/experimenter/tests/integration/test-reports

firefox --version

poetry -C experimenter/tests/integration install --no-root
poetry -C experimenter/tests/integration \
    -vvv \
    run \
    pytest \
    --html=experimenter/tests/integration/test-reports/report.htm \
    --self-contained-html \
    --reruns-delay 30 \
    --driver Firefox \
    --verify-base-url \
    --base-url https://nginx/nimbus/ \
    experimenter/tests/integration/nimbus \
    -vvv \
    $PYTEST_ARGS
