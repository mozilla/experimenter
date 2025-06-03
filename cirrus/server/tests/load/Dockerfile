# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM python:3.13-slim-bookworm

LABEL org.opencontainers.image.authors="experimenter-team@mozilla.com"

# Add gcc since there are no wheels for some packages for arm64/aarch64
# (g++/make for gevent on pypy)
RUN apt-get update && apt-get install -y git && \
  apt install -y --no-install-recommends build-essential python3-dev

ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

ENV PYTHON_VENV=/venv
RUN python -m venv ${PYTHON_VENV}
ENV PATH="${PYTHON_VENV}/bin:${PATH}"

RUN python -m pip install --upgrade pip

RUN pip install locust

RUN useradd --create-home locust
WORKDIR /home/locust

COPY ./cirrus/server/tests/load/locustfile.py ./tests/load/locustfiles/locustfile.py

# Expose ports for the web UI and the locust master
EXPOSE 8089 5557

USER locust
ENTRYPOINT locust -f "tests/load/locustfiles/locustfile.py"
