#-------------------------
FROM alpine:3.12.0 as file-loader

# To preserve layer caching across machines which may have different local file properties
# such as permissions, timestamps, etc, all files are copied into a container and their
# permissions and timestamps are reset to consistent values
# Credit: https://gist.github.com/kekru/8ac61cd87536a4355220b56ae2f4b0a9
COPY . /schemas/
RUN chmod -R 555 /schemas \
    && chown -R root:root /schemas \
    && find /schemas -exec touch -a -m -t 201512180130.09 {} \;


#-------------------------
# System packages
FROM python:3.11.1 AS system-builder

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
ENV PYTHONDONTWRITEBYTECODE 1

# Python packages
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.6.0
ENV PATH "/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false


# Python image
#-------------------------
FROM system-builder AS python-builder
WORKDIR /schemas

COPY --from=file-loader /schemas/pyproject.toml /schemas/pyproject.toml
COPY --from=file-loader /schemas/poetry.lock /schemas/poetry.lock
COPY --from=file-loader /schemas/mozilla_nimbus_schemas /schemas/mozilla_nimbus_schemas
COPY --from=file-loader /schemas/README.md /schemas/README.md
RUN poetry install

# If any package is installed, that is incompatible by version, this command
# will exit non-zero and print what is usually just a warning in `poetry install`
RUN poetry check


# Node image
#-------------------------
FROM system-builder AS node-builder
WORKDIR /schemas

# Node packages for legacy and nimbus ui
COPY --from=file-loader /schemas/package.json /schemas/package.json
COPY --from=file-loader /schemas/yarn.lock /schemas/yarn.lock
RUN yarn install --frozen-lockfile


# Dev image
#-------------------------
FROM system-builder AS dev
WORKDIR /schemas

# Python packages
COPY --from=python-builder /usr/local/bin/ /usr/local/bin/
COPY --from=python-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Node packages
COPY --from=node-builder /schemas/node_modules/ /schemas/node_modules/
