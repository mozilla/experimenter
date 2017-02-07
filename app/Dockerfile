FROM python:3.6-alpine

RUN addgroup -S app && adduser -S -g app app

ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

EXPOSE 7001

# Wait for the db to initialize
COPY bin/wait-for-it.sh /app/bin/wait-for-it.sh
RUN chmod a+x /app/bin/wait-for-it.sh

# S3 bucket in Cloud Services prod IAM
COPY bin/dumb-init /usr/local/bin/dumb-init
RUN chmod a+x /usr/local/bin/dumb-init
ENTRYPOINT ["/usr/local/bin/dumb-init", "--"]

RUN apk add --no-cache gcc musl-dev postgresql-dev postgresql-client bash uwsgi

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt --no-cache-dir --disable-pip-version-check

COPY . /app

RUN chown -R app /app
RUN chgrp -R app /app

USER app
