FROM debian:bullseye
WORKDIR /application-services

COPY . .

RUN apt-get update && \
    apt-get upgrade && \
    apt-get install -y \
        curl \
        jq \
        zip && \
    ./fetch-application-services.sh
