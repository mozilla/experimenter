#!/bin/bash

set -euo pipefail
set +x

mkdir -m a+rwx /code/experimenter/tests/integration/test-reports

poetry -C experimenter/tests/integration -vvv install --no-root

# Build pytest command with optional test splitting using pytest-test-groups
PYTEST_ARGS="--verify-base-url --base-url https://nginx/nimbus/ --html=test-reports/report.htm --self-contained-html -n 2"

# Add test group splitting if environment variables are set
if [ -n "${PYTEST_SPLIT_INDEX:-}" ] && [ -n "${PYTEST_SPLIT_TOTAL:-}" ]; then
    # pytest-test-groups uses 1-based indexing, so add 1 to CIRCLE_NODE_INDEX
    PYTEST_ARGS="$PYTEST_ARGS --test-group-count $PYTEST_SPLIT_TOTAL --test-group=$((PYTEST_SPLIT_INDEX + 1))"
fi

poetry -C experimenter/tests/integration \
    -vvv \
    run \
    pytest \
    $PYTEST_ARGS \
    /code/experimenter/tests/integration/nimbus/test_mobile_targeting.py \
    -vvv
