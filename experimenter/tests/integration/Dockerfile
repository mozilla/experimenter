FROM python:3.11-bullseye

COPY --from=experimenter:megazords \
    /application-services/megazords/nimbus-experimenter /application-services/nimbus_megazord

ENV PYTHONPATH=$PYTHONPATH:/application-services/

RUN apt-get update -qqy && \
    apt-get install -qqy \
        python3-venv \
        python3-pip

COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /usr/local/bin/

WORKDIR /code
