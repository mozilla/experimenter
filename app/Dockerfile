FROM python:3.8.0

ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

EXPOSE 7001

# Wait for the db to initialize
COPY bin/wait-for-it.sh /app/bin/wait-for-it.sh
RUN chmod +x /app/bin/wait-for-it.sh

RUN apt-get update
RUN apt-get install -y postgresql-client

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get install -y nodejs

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update && apt-get install yarn

COPY ./requirements /app/requirements

RUN pip install -r requirements/default.txt --no-cache-dir --disable-pip-version-check

# If any package is installed, that is incompatible by version, this command
# will exit non-zero and print what is usually just a warning in `pip install`
RUN pip check

COPY ./package.json /app/package.json
COPY ./yarn.lock /app/yarn.lock
RUN yarn install

COPY ./experimenter/static/ /app/experimenter/static/
RUN yarn build

COPY . /app
