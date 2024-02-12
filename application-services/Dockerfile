FROM debian:bullseye-20240130
WORKDIR /application-services

COPY . .

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    curl \
    jq \
    zip && \
    ./fetch-application-services.sh
