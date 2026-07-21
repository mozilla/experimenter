#!/bin/bash

set -euo pipefail
set +x

export UV_PROJECT_ENVIRONMENT=/tmp/uv-venv

mkdir -m a+rwx /code/experimenter/tests/integration/test-reports

uv sync --directory experimenter/tests/integration --no-install-project
uv run --directory experimenter/tests/integration \
    pytest \
    --verify-base-url \
    --base-url https://nginx/nimbus/ \
    --html=test-reports/report.htm \
    --self-contained-html \
    -n 3 \
    /code/experimenter/tests/integration/nimbus/test_mobile_targeting.py \
    -vvv
