#!/bin/bash

set -euo pipefail

hg pull && hg update

period_output() {
  while true
  do
    echo -n ".\n"
    sleep 30
  done
}

period_output &
period_pid=$!

./mach --no-interactive bootstrap --application-choice="GeckoView/Firefox for Android"
./mach build
cd mobile/android/fenix
./gradlew clean app:assembleFenixDebug
mv app/build/outputs/apk/fenix/debug/app-fenix-x86_64-debug.apk ./
./gradlew clean app:assembleFenixDebugAndroidTest
mv app/build/outputs/apk/androidTest/fenix/debug/app-fenix-debug-androidTest.apk ./
kill $period_pid
