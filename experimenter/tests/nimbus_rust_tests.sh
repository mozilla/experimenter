#!/bin/bash

set -euo pipefail
set +x

mkdir -m a+rwx /code/experimenter/tests/integration/test-reports

poetry -C experimenter/tests/integration -vvv install --no-root
poetry -C experimenter/tests/integration \
    -vvv \
    run \
    pytest \
    --verify-base-url \
    --base-url https://nginx/nimbus/ \
    --html=test-reports/report.htm \
    --self-contained-html \
    -n 3 \
    /code/experimenter/tests/integration/nimbus/test_mobile_targeting.py \
    -vvv
