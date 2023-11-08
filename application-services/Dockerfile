FROM debian:bullseye AS as-builder
WORKDIR /application-services

RUN apt-get update && \
    apt-get upgrade && \
    apt-get install -y \
      curl \
      jq \
      zip

COPY . /application-services
RUN ./fetch-application-services.sh
