#!/bin/bash

set -euo pipefail

cd mobile/android/fenix \
&& ./gradlew clean app:assembleFenixDebug \
&& mv app/build/outputs/apk/fenix/debug/app-fenix-x86-debug.apk ./ \
&& ./gradlew clean app:assembleFenixDebugAndroidTest \
&& mv app/build/outputs/apk/androidTest/fenix/debug/app-fenix-debug-androidTest.apk ./