FROM python:3.11-bullseye

COPY --from=experimenter:megazords \
    /application-services/megazords/nimbus-experimenter /application-services/nimbus_megazord

ENV PYTHONPATH=$PYTHONPATH:/application-services/

RUN apt-get update -qqy && \
    apt-get install -qqy \
        tox

WORKDIR /code
