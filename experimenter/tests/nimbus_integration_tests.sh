#!/bin/bash

set -euo pipefail
set +x

export PATH=$PATH:/home/seluser/.local/bin

if [[ -n "${UPDATE_FIREFOX_VERSION}" ]]; then
    sudo ./experimenter/tests/integration/nimbus/utils/nightly-install.sh
fi

curl -sSL https://install.python-poetry.org | python3 - --version 1.8.3
sudo chmod -R a+rwx /code/experimenter/tests/integration/
mkdir -m a+rwx /code/experimenter/tests/integration/test-reports

poetry -C experimenter/tests/integration -vvv install --no-root
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
