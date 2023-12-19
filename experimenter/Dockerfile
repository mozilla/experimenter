#-------------------------
FROM alpine:3.12.0 as file-loader

# To preserve layer caching across machines which may have different local file properties
# such as permissions, timestamps, etc, all files are copied into a container and their
# permissions and timestamps are reset to consistent values
# Credit: https://gist.github.com/kekru/8ac61cd87536a4355220b56ae2f4b0a9
COPY . /experimenter/
RUN chmod -R 555 /experimenter \
    && chown -R root:root /experimenter \
    && find /experimenter -exec touch -a -m -t 201512180130.09 {} \;


#-------------------------
# System packages
FROM python:3.11.1 AS system-builder

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
ENV PYTHONDONTWRITEBYTECODE 1

# Python packages
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.6.0
ENV PATH "/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false

# Rust cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | /bin/sh -s -- -y --profile minimal
ENV PATH "/root/.cargo/bin:$PATH"

# Python image
#-------------------------
FROM system-builder AS python-builder
WORKDIR /experimenter

COPY --from=file-loader /experimenter/pyproject.toml /experimenter/pyproject.toml
COPY --from=file-loader /experimenter/poetry.lock /experimenter/poetry.lock
RUN poetry install

# If any package is installed, that is incompatible by version, this command
# will exit non-zero and print what is usually just a warning in `poetry install`
RUN poetry check


# Node image
#-------------------------
FROM system-builder AS node-builder
WORKDIR /experimenter

# Node packages for legacy and nimbus ui
COPY --from=file-loader /experimenter/package.json /experimenter/package.json
COPY --from=file-loader /experimenter/yarn.lock /experimenter/yarn.lock
COPY --from=file-loader /experimenter/experimenter/legacy/legacy-ui/core/package.json /experimenter/experimenter/legacy/legacy-ui/core/package.json
COPY --from=file-loader /experimenter/experimenter/nimbus-ui/package.json /experimenter/experimenter/nimbus-ui/package.json
RUN yarn install --frozen-lockfile

# Node packages for htmx ui
COPY --from=file-loader /experimenter/experimenter/theme/static_src/package.json /experimenter/experimenter/theme/static_src/package.json
COPY --from=file-loader /experimenter/experimenter/theme/static_src/yarn.lock /experimenter/experimenter/theme/static_src/yarn.lock
RUN yarn install --frozen-lockfile --cwd /experimenter/experimenter/theme/static_src



# Rust image
#-------------------------
FROM system-builder AS rust-builder
WORKDIR /application-services

# Rust packages
# Checkout application services at a locked commit
RUN git clone https://github.com/mozilla/application-services.git .
RUN git fetch && git checkout 1f11e95bf478666ca49c279a8927931c5535a786

RUN git submodule init
RUN git submodule update --recursive

RUN mkdir -p /application-services/megazord

RUN cargo build --manifest-path /application-services/megazords/nimbus-experimenter/Cargo.toml --release
RUN cargo uniffi-bindgen generate --library /application-services/target/release/libnimbus_experimenter.so --language python --out-dir /application-services/megazord

# Dev image
#-------------------------
FROM system-builder AS dev
WORKDIR /experimenter

# Scripts for waiting for the db and setting up kinto
COPY --from=file-loader /experimenter/bin/ /experimenter/bin/
RUN chmod +x /experimenter/bin/wait-for-it.sh

# Python packages
COPY --from=python-builder /usr/local/bin/ /usr/local/bin/
COPY --from=python-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Node packages
COPY --from=node-builder /experimenter/experimenter/legacy/legacy-ui/core/node_modules/ /experimenter/experimenter/legacy/legacy-ui/core/node_modules/
COPY --from=node-builder /experimenter/experimenter/theme/static_src/node_modules/ /experimenter/experimenter/theme/static_src/node_modules/
COPY --from=node-builder /experimenter/experimenter/nimbus-ui/node_modules/ /experimenter/experimenter/nimbus-ui/node_modules/
COPY --from=node-builder /experimenter/node_modules/ /experimenter/node_modules/

# Rust packages
COPY --from=rust-builder /application-services/megazord/fml.py /application-services/megazord/rust_fml.py
COPY --from=rust-builder /application-services/megazord/nimbus.py /application-services/megazord/rust_sdk.py
COPY --from=rust-builder /application-services/megazord/errorsupport.py /application-services/megazord/rust_errorsupport.py
COPY --from=rust-builder /application-services/megazord/remote_settings.py /application-services/megazord/rust_remote_settings.py
# The uniffi.toml file setting cdylib_name is set to "cirrus", which means the generated python is expecting
# the library to be called libcirrus.so.
COPY --from=rust-builder /application-services/target/release/libnimbus_experimenter.so /application-services/megazord/libcirrus.so
ENV PYTHONPATH=$PYTHONPATH:/application-services/megazord

# Install nimbus-cli

RUN mkdir -p /application-services/bin/ && \
    curl --proto '=https' --tlsv1.2 -sSf -o "/application-services/install-nimbus-cli.sh" "https://raw.githubusercontent.com/mozilla/application-services/main/install-nimbus-cli.sh" && \
    bash /application-services/install-nimbus-cli.sh --directory /application-services/bin

#-------------------------
FROM dev AS test

# Copy source
COPY --from=file-loader /experimenter/ /experimenter/


# Build image
#-------------------------
FROM test AS ui

# Build legacy assets
COPY --from=file-loader /experimenter/experimenter/legacy/legacy-ui/* /experimenter/experimenter/legacy/legacy-ui/
RUN yarn workspace @experimenter/core build

# Build nimbus ui assets
COPY --from=file-loader /experimenter/experimenter/nimbus-ui/ /experimenter/experimenter/nimbus-ui/
RUN yarn workspace @experimenter/nimbus-ui build

# Build static assets
COPY --from=file-loader /experimenter/experimenter/theme/ /experimenter/experimenter/theme/
COPY --from=file-loader /experimenter/experimenter/templates/ /experimenter/experimenter/templates/
RUN yarn --cwd /experimenter/experimenter/theme/static_src build


# Deploy image
#-------------------------
FROM python:3.11.1-slim AS deploy

WORKDIR /experimenter
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
COPY --from=dev /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=dev /experimenter/bin/ /experimenter/bin/
COPY --from=dev /application-services/megazord/ /application-services/megazord/
COPY --from=file-loader /experimenter/manage.py /experimenter/manage.py
COPY --from=file-loader /experimenter/experimenter/ /experimenter/experimenter/
COPY --from=file-loader /experimenter/manifesttool/ /experimenter/manifesttool/
COPY --from=ui /experimenter/experimenter/legacy/legacy-ui/assets/ /experimenter/experimenter/legacy/legacy-ui/assets/
COPY --from=ui /experimenter/experimenter/nimbus-ui/build/ /experimenter/experimenter/nimbus-ui/build/
COPY --from=ui /experimenter/experimenter/theme/static/ /experimenter/experimenter/theme/static/
COPY --from=ui /experimenter/experimenter/static/scripts/ /experimenter/experimenter/static/scripts/
ENV PYTHONPATH=$PYTHONPATH:/application-services/megazord
