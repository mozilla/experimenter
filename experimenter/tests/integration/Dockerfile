FROM python:3.11-bullseye

COPY --from=experimenter:megazords \
    /application-services/megazords/nimbus-experimenter /application-services/megazord
RUN mv /application-services/megazord/nimbus.py /application-services/megazord/nimbus_rust.py

RUN apt-get update -qqy && \
    apt-get install -qqy \
        tox

WORKDIR /code
