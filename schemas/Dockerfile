FROM alpine:3.12.0 as file-loader

# To preserve layer caching across machines which may have different local file properties
# such as permissions, timestamps, etc, all files are copied into a container and their
# permissions and timestamps are reset to consistent values
# Credit: https://gist.github.com/kekru/8ac61cd87536a4355220b56ae2f4b0a9
COPY . /schemas/
RUN chmod -R 555 /schemas \
  && chown -R root:root /schemas \
  && find /schemas -exec touch -a -m -t 201512180130.09 {} \;


# Dev image
FROM python:3.11.1 AS dev

WORKDIR /schemas


# Install nvm with node and npm
ENV NODE_VERSION=16.19.0
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"


# System  packages
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates yarn


# Python packages
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false
COPY --from=file-loader /schemas/pyproject.toml /schemas/pyproject.toml
COPY --from=file-loader /schemas/poetry.lock /schemas/poetry.lock
RUN poetry install

# If any package is installed, that is incompatible by version, this command
# will exit non-zero and print what is usually just a warning in `poetry install`
RUN poetry check


# Node packages
COPY --from=file-loader /schemas/package.json /schemas/package.json
COPY --from=file-loader /schemas/yarn.lock /schemas/yarn.lock
RUN yarn install --frozen-lockfile


# Deploy image
FROM python:3.11.1-slim AS deploy

WORKDIR /schemas


# Add poetry to path
ENV PATH "/root/.poetry/bin:${PATH}"


# System packages
RUN apt-get update
RUN apt-get --no-install-recommends install -y apt-utils ca-certificates postgresql-client


# Copy source from previously built containers
COPY --from=dev /usr/local/bin/ /usr/local/bin/
COPY --from=dev /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=dev /schemas /schemas
