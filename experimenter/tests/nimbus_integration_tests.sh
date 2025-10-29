#!/bin/bash

set -euo pipefail
set +x

export PATH=$PATH:/home/seluser/.local/bin

PYTEST_ARGS=${PYTEST_ARGS:-"-k FIREFOX_DESKTOP"}
FIREFOX_CHANNEL=${FIREFOX_CHANNEL:-"release"}

install_firefox() {
    local firefox_version="$1"
    echo $firefox_version
    sudo apt-get update -qqy
    sudo apt-get install xz-utils
    sudo rm -rf /var/lib/apt/lists/* /var/cache/apt/*
    sudo wget --no-verbose -O /tmp/firefox $firefox_version
    sudo rm -rf /opt/firefox-latest
    sudo tar -C /opt -xf /tmp/firefox
    sudo rm /tmp/firefox
    sudo ln -fs /opt/firefox/firefox /usr/bin/firefox
    sudo chown -R seluser /opt/firefox/firefox
}

case "$FIREFOX_CHANNEL" in
  nightly)
    sudo ./experimenter/tests/integration/nimbus/utils/nightly-install.sh
    ;;
  beta)
    source ./experimenter/tests/firefox_desktop_beta_build.env
    FIREFOX_DESKTOP_BETA_TASK_ID=${FIREFOX_DESKTOP_BETA_TASK_ID//\"/}
    echo "Installing firefox beta from taskcluster"
    install_firefox "https://firefox-ci-tc.services.mozilla.com/api/queue/v1/task/${FIREFOX_DESKTOP_BETA_TASK_ID}/artifacts/public/build/target.tar.xz"
    ;;
  release)
    source ./experimenter/tests/firefox_desktop_release_build.env
    FIREFOX_DESKTOP_RELEASE_VERSION_ID=${FIREFOX_DESKTOP_RELEASE_VERSION_ID//\"/}
    echo "Installing firefox release v${FIREFOX_DESKTOP_RELEASE_VERSION_ID}"
    install_firefox "https://ftp.mozilla.org/pub/firefox/releases/${FIREFOX_DESKTOP_RELEASE_VERSION_ID}/linux-x86_64/en-US/firefox-${FIREFOX_DESKTOP_RELEASE_VERSION_ID}.tar.xz"
    ;;
  *)
    echo "Unknown FIREFOX_CHANNEL: '$FIREFOX_CHANNEL'"
    exit 1
    ;;
esac

curl -sSL https://install.python-poetry.org | python3 - --version 1.8.4
sudo chmod -R a+rwx /code/experimenter/tests/integration/
mkdir -m a+rwx -p /code/experimenter/tests/integration/test-reports
sudo chown -R seluser /opt/venv/

firefox --version

# Ensure proper permissions for X11 socket directory
sudo mkdir -p /tmp/.X11-unix
sudo chmod 1777 /tmp/.X11-unix

# Start Xvfb in the background
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!
export DISPLAY=:99

# Wait for Xvfb to start
sleep 2

poetry -C experimenter/tests/integration install --no-root
poetry -C experimenter/tests/integration \
    run \
    pytest \
    --html=experimenter/tests/integration/test-reports/report.htm \
    --self-contained-html \
    --reruns-delay 30 \
    --driver Firefox \
    --verify-base-url \
    experimenter/tests/integration/nimbus \
    -vvv \
    $PYTEST_ARGS

# Clean up Xvfb process
kill $XVFB_PID 2>/dev/null || true
