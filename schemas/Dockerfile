#-------------------------
# System packages
FROM python:3.10.14 AS system-builder

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates yarn parallel

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
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.1.1
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false


# Python image
#-------------------------
FROM system-builder AS python-builder
WORKDIR /schemas

# Poetry needs a package to install in package-mode.
RUN mkdir mozilla_nimbus_schemas && \
    touch mozilla_nimbus_schemas/__init__.py

COPY ./pyproject.toml /schemas/pyproject.toml
COPY ./poetry.lock /schemas/poetry.lock
COPY ./README.md /schemas/README.md

RUN poetry install

# If any package is installed, that is incompatible by version, this command
# will exit non-zero and print what is usually just a warning in `poetry install`
RUN poetry check

COPY ./mozilla_nimbus_schemas /schemas/mozilla_nimbus_schemas

# Node image
#-------------------------
FROM system-builder AS node-builder
WORKDIR /schemas

# Node packages for legacy and nimbus ui
COPY ./package.json /schemas/package.json
COPY ./yarn.lock /schemas/yarn.lock
RUN yarn install --frozen-lockfile


# Dev image
#-------------------------
FROM system-builder AS dev
WORKDIR /schemas

# Python packages
COPY --from=python-builder /usr/local/bin/ /usr/local/bin/
COPY --from=python-builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Node packages
COPY --from=node-builder /schemas/node_modules/ /schemas/node_modules/
