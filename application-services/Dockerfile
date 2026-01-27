FROM debian:bullseye-20240130
WORKDIR /application-services

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y curl jq zip

COPY . .

RUN ./fetch-application-services.sh
