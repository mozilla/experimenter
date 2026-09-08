FROM debian:trixie-slim
WORKDIR /application-services

RUN apt-get update && \
    apt-get install -y curl jq zip

COPY . .

RUN ./fetch-application-services.sh
