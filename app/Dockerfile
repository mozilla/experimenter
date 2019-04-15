FROM python:3.7.3

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

# If any package is installed, that is incompatible by version, this command
# will exit non-zero and print what is usually just a warning in `pip install`
RUN pip check

COPY . /app
