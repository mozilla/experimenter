FROM alpine:latest

WORKDIR /usr/src/app

RUN mkdir -p /usr/src/app/files

COPY app-fenix-debug-androidTest.apk /usr/src/app/files/
COPY app-fenix-x86_64-debug.apk /usr/src/app/files/
