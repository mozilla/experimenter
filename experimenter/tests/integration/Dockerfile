FROM python:3.11-bullseye

COPY --from=megazords /application-services/megazords/nimbus-experimenter /application-services/nimbus_megazord

ENV PYTHONPATH=$PYTHONPATH:/application-services/

RUN apt-get update -qqy && \
    apt-get install -qqy \
        python3-venv \
        python3-pip

RUN pip install poetry==1.8.4

WORKDIR /code
