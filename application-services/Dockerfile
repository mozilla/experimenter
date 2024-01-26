FROM debian:bullseye
WORKDIR /application-services

COPY . .

RUN apt-get update && \
    apt-get upgrade && \
    apt-get install -y \
        curl \
        zip && \
    ./fetch-application-services.sh
