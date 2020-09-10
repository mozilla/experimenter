FROM python:3.8.2

# Disable python pyc files
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

EXPOSE 7001

# Script for waiting for the db to initialize
COPY bin/wait-for-it.sh /app/bin/wait-for-it.sh
RUN chmod +x /app/bin/wait-for-it.sh

# System  packages
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates postgresql-client nodejs yarn parallel



# Python packages
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
ENV PATH "/root/.poetry/bin:${PATH}"

# Make and activate a Python virtualenv
RUN python -m venv /opt/venv
ENV PATH "/opt/venv/bin:${PATH}"
ENV VIRTUAL_ENV="/opt/venv"

COPY poetry.lock pyproject.toml ./
RUN poetry install


# If any package is installed, that is incompatible by version, this command
RUN poetry check

# Node packages
COPY ./package.json /app/package.json
COPY ./yarn.lock /app/yarn.lock
COPY ./experimenter/static/core/package.json /app/experimenter/static/core/package.json
COPY ./experimenter/static/rapid/package.json /app/experimenter/static/rapid/package.json
RUN yarn install --frozen-lockfile

# Build assets
COPY ./experimenter/static/ /app/experimenter/static/
RUN yarn workspace @experimenter/core build
RUN yarn workspace @experimenter/rapid build

# Copy source
COPY . /app
