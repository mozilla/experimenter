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

# RUN cd mobile/android/fenix \
#     && ./gradlew clean app:assembleFenixDebug \
#     && mv app/build/outputs/apk/fenix/debug/app-fenix-x86_64-debug.apk ./ \
#     && ./gradlew clean app:assembleFenixDebugAndroidTest \
#     && mv app/build/outputs/apk/androidTest/fenix/debug/app-fenix-debug-androidTest.apk ./


# # Install pipenv
# RUN pip install pipenv

# /root/.mozbuild/android-sdk-linux/

# docker cp 57f0dfc40252459e47aadd58ff59fa0fd7a8c209cb23df08c675694ef503d763:mozilla-central/mobile/android/fenix/app-fenix-debug-androidTest.apk ./
# docker cp 57f0dfc40252459e47aadd58ff59fa0fd7a8c209cb23df08c675694ef503d763:mozilla-central/mobile/android/fenix/app-fenix-x86_64-debug.apk ./

# NEED TO NAME WHEN CONTAINER RUNS