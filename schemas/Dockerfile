#-------------------------
# System packages
FROM python:3.10.14 AS system-builder

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates yarn parallel

# Install nvm with node and npm
ENV NODE_VERSION=24.14.0
ENV NVM_DIR=/root/.nvm
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.35.3/install.sh | bash
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}

# Disable python pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Python packages
COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /usr/local/bin/


# Python image
#-------------------------
FROM system-builder AS python-builder
WORKDIR /schemas

COPY ./pyproject.toml /schemas/pyproject.toml
COPY ./uv.lock /schemas/uv.lock
COPY ./README.md /schemas/README.md

# Install dependencies into a virtualenv that later stages can copy
ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync --frozen --no-install-project

COPY ./mozilla_nimbus_schemas /schemas/mozilla_nimbus_schemas
RUN uv sync --frozen

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
COPY --from=python-builder /opt/venv/ /opt/venv/
ENV PATH="/opt/venv/bin:$PATH"

# Node packages
COPY --from=node-builder /schemas/node_modules/ /schemas/node_modules/
