#!/bin/bash

set -euo pipefail
set +x

export PATH=$PATH:/home/seluser/.local/bin

apt-get -qqy update && apt-get -qqy install python3-venv python3-pip
pip install poetry
mkdir -m a+rwx /code/experimenter/tests/integration/test-reports

poetry -C experimenter/tests/integration -vvv install --no-root
poetry -C experimenter/tests/integration run pytest --verify-base-url --base-url https://nginx/nimbus/ --html=test-reports/report.htm --self-contained-html experimenter/tests/integration/nimbus/test_mobile_targeting.py -vvv
