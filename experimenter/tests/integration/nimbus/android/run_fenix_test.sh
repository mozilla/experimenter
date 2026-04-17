#!/usr/bin/env bash
set -euo pipefail

: "${FENIX_APK_PATH:?must be set}"
: "${FENIX_RECIPE_PATH:?must be set}"
: "${FENIX_EXPERIMENT_SLUG:?must be set}"

FENIX_PACKAGE=org.mozilla.fenix.debug
NIMBUS_LOG_TAG=app-services-Nimbus.kt

echo "=== Install Fenix debug APK ==="
adb install -r -t -g "$FENIX_APK_PATH"
adb shell pm list packages "$FENIX_PACKAGE"

echo "=== Clear logcat buffer ==="
adb logcat -c

echo "=== nimbus-cli enroll (preserve targeting + bucketing) ==="
nimbus-cli \
    --app fenix \
    --channel developer \
    enroll "$FENIX_EXPERIMENT_SLUG" \
    --branch control \
    --file "$FENIX_RECIPE_PATH" \
    --preserve-targeting \
    --preserve-bucketing \
    --reset-app \
    --no-validate

echo "=== Wait for app + Nimbus SDK to apply experiments ==="
sleep 15

echo "=== nimbus-cli log-state (dumps enrollment state to logcat) ==="
nimbus-cli --app fenix --channel developer log-state
sleep 5

echo "=== Dump logcat ==="
adb logcat -d > logcat.txt
echo "logcat size: $(wc -l < logcat.txt) lines"

echo "=== Nimbus log lines ==="
grep -E "$NIMBUS_LOG_TAG|NimbusTooling|nimbus_client" logcat.txt | tail -100 || true

echo "=== Assert enrollment line for $FENIX_EXPERIMENT_SLUG ==="
if grep -E "$NIMBUS_LOG_TAG.*$FENIX_EXPERIMENT_SLUG" logcat.txt; then
    echo "PASS: found enrollment state line"
    exit 0
fi

if grep -E "$FENIX_EXPERIMENT_SLUG" logcat.txt; then
    echo "FAIL: found slug references but no nimbus log-state line"
    exit 1
fi

echo "FAIL: no references to $FENIX_EXPERIMENT_SLUG in logcat"
exit 1
