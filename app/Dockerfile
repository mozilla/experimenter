FROM alpine:3.12.0 as file-loader

# To preserve layer caching across machines which may have different local file properties
# such as permissions, timestamps, etc, all files are copied into a container and their
# permissions and timestamps are reset to consistent values
# Credit: https://gist.github.com/kekru/8ac61cd87536a4355220b56ae2f4b0a9
COPY . /app/
RUN chmod -R 555 /app \
    && chown -R root:root /app \
    && find /app -exec touch -a -m -t 201512180130.09 {} \;


# Dev image
FROM python:3.10 AS dev

WORKDIR /app


# Disable python pyc files
ENV PYTHONDONTWRITEBYTECODE 1


# Scripts for waiting for the db and setting up kinto
COPY --from=file-loader /app/bin/ /app/bin/
RUN chmod +x /app/bin/wait-for-it.sh


# Install nvm with node and npm
ENV NODE_VERSION=14.17.1
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.35.3/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"


# System  packages
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates postgresql-client yarn parallel


# Python packages
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false
COPY --from=file-loader /app/pyproject.toml /app/pyproject.toml
COPY --from=file-loader /app/poetry.lock /app/poetry.lock
RUN poetry install

# If any package is installed, that is incompatible by version, this command
# will exit non-zero and print what is usually just a warning in `poetry install`
RUN poetry check


# Node packages
COPY --from=file-loader /app/package.json /app/package.json
COPY --from=file-loader /app/yarn.lock /app/yarn.lock
COPY --from=file-loader /app/experimenter/legacy/legacy-ui/core/package.json /app/experimenter/legacy/legacy-ui/core/package.json
RUN yarn install --frozen-lockfile

COPY --from=file-loader /app/experimenter/nimbus-ui/package.json /app/experimenter/nimbus-ui/package.json
RUN yarn install --frozen-lockfile


FROM dev AS test

# Copy source
COPY --from=file-loader /app/ /app/


# Build image
FROM dev AS ui


# Build assets
COPY --from=file-loader /app/experimenter/legacy/legacy-ui/ /app/experimenter/legacy/legacy-ui/
RUN yarn workspace @experimenter/core build
COPY --from=file-loader /app/experimenter/nimbus-ui/ /app/experimenter/nimbus-ui/
RUN yarn workspace @experimenter/nimbus-ui build

# Deploy image
FROM python:3.10-slim AS deploy

WORKDIR /app
EXPOSE 7001

# Disable python pyc files
ENV PYTHONDONTWRITEBYTECODE 1


# Add poetry to path
ENV PATH "/root/.poetry/bin:${PATH}"


# System packages
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates postgresql-client


# Copy source from previously built containers
COPY --from=dev /usr/local/bin/ /usr/local/bin/
COPY --from=dev /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=dev /app/bin/ /app/bin/
COPY --from=file-loader /app/manage.py /app/manage.py
COPY --from=file-loader /app/experimenter/ /app/experimenter/
COPY --from=ui /app/experimenter/legacy/legacy-ui/assets/ /app/experimenter/legacy/legacy-ui/assets/
COPY --from=ui /app/experimenter/nimbus-ui/build/ /app/experimenter/nimbus-ui/build/
