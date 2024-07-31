#!/bin/bash

set -euo pipefail

git pull

./mach --no-interactive bootstrap --application-choice="GeckoView/Firefox for Android Artifact Mode"
./mach clobber
./mach build
cd mobile/android/fenix
./gradlew clean app:assembleFenixDebug
mv app/build/outputs/apk/fenix/debug/app-fenix-x86_64-debug.apk ./
./gradlew clean app:assembleFenixDebugAndroidTest
mv app/build/outputs/apk/androidTest/fenix/debug/app-fenix-debug-androidTest.apk ./
