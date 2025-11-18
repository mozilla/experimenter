#-------------------------
# System packages
FROM python:3.13-bullseye AS system-builder

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates postgresql-client yarn parallel

# Install nvm with node and npm
ENV NODE_VERSION=16.19.0
ENV NVM_DIR=/root/.nvm
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.35.3/install.sh | bash
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}

# Disable python pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Python packages
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.2.1
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false

# Rust cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | /bin/sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:$PATH"

# Python image
#-------------------------
FROM system-builder AS python-builder
WORKDIR /experimenter

COPY ./pyproject.toml /experimenter/pyproject.toml
COPY ./poetry.lock /experimenter/poetry.lock
RUN poetry install

# If any package is installed, that is incompatible by version, this command
# will exit non-zero and print what is usually just a warning in `poetry install`
RUN poetry check

# Build glean assets
COPY ./experimenter/telemetry /experimenter/experimenter/telemetry
RUN glean_parser translate experimenter/telemetry/pings.yaml experimenter/telemetry/metrics.yaml -f python_server -o experimenter/glean/generated

# Node image
#-------------------------
FROM system-builder AS node-builder
WORKDIR /experimenter

# Node packages for legacy and nimbus ui
COPY ./package.json /experimenter/package.json
COPY ./yarn.lock /experimenter/yarn.lock
COPY ./experimenter/legacy/legacy-ui/core/package.json /experimenter/experimenter/legacy/legacy-ui/core/package.json
COPY ./experimenter/results/package.json /experimenter/experimenter/results/package.json
COPY ./experimenter/nimbus_ui/static/package.json /experimenter/experimenter/nimbus_ui/static/package.json
RUN python3 -m pip install setuptools
RUN yarn install --frozen-lockfile
COPY ./experimenter/legacy/legacy-ui/core/ /experimenter/experimenter/legacy/legacy-ui/core/
COPY ./experimenter/results/ /experimenter/experimenter/results/
COPY ./experimenter/nimbus_ui/ /experimenter/experimenter/nimbus_ui/


# Dev image
#-------------------------
FROM system-builder AS dev
WORKDIR /experimenter

# Scripts for waiting for the db and setting up kinto
COPY ./bin/ /experimenter/bin/
RUN chmod +x /experimenter/bin/wait-for-it.sh

# Python packages
COPY --from=python-builder /usr/local/bin/ /usr/local/bin/
COPY --from=python-builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=python-builder /experimenter/experimenter/glean/generated/ /experimenter/experimenter/glean/generated/

# Node packages
COPY --from=node-builder /experimenter/experimenter/legacy/legacy-ui/core/node_modules/ /experimenter/experimenter/legacy/legacy-ui/core/node_modules/
COPY --from=node-builder /experimenter/experimenter/results/node_modules/ /experimenter/experimenter/results/node_modules/
COPY --from=node-builder /experimenter/experimenter/nimbus_ui/static/node_modules/ /experimenter/experimenter/nimbus_ui/static/node_modules/
COPY --from=node-builder /experimenter/node_modules/ /experimenter/node_modules/

# Rust packages
COPY --from=experimenter:megazords /application-services/megazords/nimbus-experimenter/ /application-services/nimbus_megazord/
ENV PYTHONPATH=$PYTHONPATH:/application-services/

# Install nimbus-cli
RUN mkdir -p /application-services/bin/ && \
    curl --proto '=https' --tlsv1.2 -sSf -o "/application-services/install-nimbus-cli.sh" "https://raw.githubusercontent.com/mozilla/application-services/main/install-nimbus-cli.sh" && \
    bash /application-services/install-nimbus-cli.sh --directory /application-services/bin

#-------------------------
FROM dev AS test

# Copy source
COPY . /experimenter/


# Build image
#-------------------------
FROM test AS ui

# Build legacy assets
COPY ./experimenter/legacy/legacy-ui/* /experimenter/experimenter/legacy/legacy-ui/
RUN yarn workspace @experimenter/core build

# Build results assets
COPY ./experimenter/results/ /experimenter/experimenter/results/
RUN yarn workspace @experimenter/results build

# Build nimbus_ui assets
COPY ./experimenter/nimbus_ui/ /experimenter/experimenter/nimbus_ui/
RUN yarn workspace @experimenter/nimbus_ui build


# Deploy image
#-------------------------
FROM python:3.13-slim AS deploy

# Create a non-root user with UID 10001
RUN groupadd -g 10001 app && \
    useradd -r -u 10001 -g app app

WORKDIR /experimenter
EXPOSE 7001

# Disable python pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# System packages
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates git postgresql-client 

# Copy source from previously built containers
COPY --from=dev /usr/local/bin/ /usr/local/bin/
COPY --from=dev /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=dev /experimenter/experimenter/glean/generated/ /experimenter/experimenter/glean/generated/
COPY --from=dev /experimenter/bin/ /experimenter/bin/
COPY --from=dev /application-services/nimbus_megazord/ /application-services/nimbus_megazord/
COPY ./manage.py /experimenter/manage.py
COPY ./experimenter/ /experimenter/experimenter/
COPY ./manifesttool/ /experimenter/manifesttool/
COPY --from=ui /experimenter/experimenter/legacy/legacy-ui/assets/ /experimenter/experimenter/legacy/legacy-ui/assets/
COPY --from=ui /experimenter/experimenter/results/build/ /experimenter/experimenter/results/build/
COPY --from=ui /experimenter/experimenter/nimbus_ui/static/dist/ /experimenter/experimenter/nimbus_ui/static/dist/

ENV PYTHONPATH=$PYTHONPATH:/application-services/
ENV PYTHONUNBUFFERED=1

# Ensure the non-root user owns the required directories
RUN chown -R app:app /experimenter /application-services

# Switch to the non-root user
USER app
