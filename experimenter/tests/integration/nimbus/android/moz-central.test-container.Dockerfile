# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM debian:bookworm-slim

# Install requirements to install tools
RUN dependencies=' \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        python3 \
        git \
        openjdk-17-jdk \
        mercurial \
        wget \
        curl \
    ' \
    && set -x \
    && apt-get -qq update && apt-get -qq install -y $dependencies && apt-get clean

ENV ANDROID_HOME=/root/.mozbuild/android-sdk-linux \
    AUTOCLOBBER=1

RUN wget https://raw.githubusercontent.com/glandium/git-cinnabar/master/download.py -O download.py \
    && chmod +x download.py \
    && ./download.py \
    && cp git-cinnabar /usr/local/bin \
    && cp git-remote-hg /usr/local/bin

RUN git clone --depth 1 hg::https://hg.mozilla.org/mozilla-central

WORKDIR mozilla-central

COPY local.properties mobile/android/fenix/
COPY build_android.sh ./

RUN ./mach --no-interactive bootstrap --application-choice="GeckoView/Firefox for Android Artifact Mode"

RUN ./mach build

RUN cd mobile/android/fenix \
    && ./gradlew clean app:assembleFenixDebug \
    && mv /mozilla-central/objdir-frontend/gradle/build/mobile/android/fenix/app/outputs/apk/fenix/debug/app-fenix-x86_64-debug.apk ./ \
    && ./gradlew clean app:assembleFenixDebugAndroidTest \
    && mv /mozilla-central/objdir-frontend/gradle/build/mobile/android/fenix/app/outputs/apk/androidTest/fenix/debug/app-fenix-debug-androidTest.apk ./
