#!/usr/bin/env bash
set -euo pipefail

: "${FENIX_APK_PATH:?must be set}"
: "${FENIX_RECIPE_PATH:?must be set}"
: "${FENIX_EXPERIMENT_SLUG:?must be set}"

FENIX_PACKAGE=org.mozilla.fenix.debug

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
grep -E "nimbus_client|NimbusTooling|app-services-Nimbus" logcat.txt | tail -100 || true

echo "=== Assert enrollment line for $FENIX_EXPERIMENT_SLUG ==="
ENROLLMENT_LINE=$(grep -E "nimbus_client:\s*$FENIX_EXPERIMENT_SLUG\s+\|" logcat.txt | tail -1 || true)
if [ -n "$ENROLLMENT_LINE" ]; then
    echo "PASS: $ENROLLMENT_LINE"
    exit 0
fi

echo "FAIL: no log-state row found for $FENIX_EXPERIMENT_SLUG"
echo "--- grep nimbus_client lines ---"
grep "nimbus_client" logcat.txt | tail -20 || true
exit 1
