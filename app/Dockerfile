FROM python:3.6

ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

EXPOSE 7001

# Wait for the db to initialize
COPY bin/wait-for-it.sh /app/bin/wait-for-it.sh
RUN chmod +x /app/bin/wait-for-it.sh

RUN apt-get update
RUN apt-get install -y postgresql-client

COPY ./requirements /app/requirements

RUN pip install -r requirements/default.txt --no-cache-dir --disable-pip-version-check

COPY . /app
