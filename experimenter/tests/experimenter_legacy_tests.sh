#!/bin/bash

set -euo pipefail
set +x

export PATH=$PATH:/home/seluser/.local/bin

sudo apt-get -qqy update && sudo apt-get -qqy install python3-venv python3-pip

# https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-break-system-packages
# we are doing this because we don't control this docker image and this allows us
# to install poetry globally
pip install poetry --break-system-packages
sudo chmod -R a+rwx /code/experimenter/tests/integration/
mkdir -m a+rwx /code/experimenter/tests/integration/test-reports

poetry -C experimenter/tests/integration -vvv install --no-root
poetry -C experimenter/tests/integration \
    -vvv run pytest \
    --html=experimenter/tests/integration/test-reports/report.htm \
    --self-contained-html \
    --reruns-delay 30 \
    --driver Firefox \
    --verify-base-url \
    --base-url https://nginx/nimbus/ \
    experimenter/tests/integration/legacy/ \
    -vvv
