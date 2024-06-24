# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM debian:stable-slim

# Install requirements to install tools
RUN dependencies=' \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        python3 \
        git \
        openjdk-17-jdk \
        mercurial \
    ' \
    && set -x \
    && apt-get -qq update && apt-get -qq install -y $dependencies && apt-get clean

ENV JAVA_HOME /root/.mozbuild/jdk/jdk-17.0.11+9
ENV ANDROID_HOME /root/.mozbuild/android-sdk-linux

RUN hg clone https://hg.mozilla.org/mozilla-central/

WORKDIR mozilla-central

COPY local.properties mobile/android/fenix/
COPY build_android.sh ./

RUN ./mach --no-interactive bootstrap --application-choice="GeckoView/Firefox for Android Artifact Mode"

RUN ./mach build
