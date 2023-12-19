# First stage: Build the Rust components
FROM rust:1.74.0-buster AS rust-builder

RUN update-ca-certificates

RUN apt-get update -qqy \
    && apt-get -qqy install \
    gyp \
    ninja-build \
    zlib1g-dev \
    tclsh \
    python3-venv

WORKDIR /application-services

# Checkout application services at a locked commit
RUN git clone https://github.com/mozilla/application-services.git .
RUN git fetch && git checkout 1f11e95bf478666ca49c279a8927931c5535a786

RUN git submodule init
RUN git submodule update --recursive

RUN cargo build --manifest-path megazords/cirrus/Cargo.toml --release
RUN cargo uniffi-bindgen generate --library target/release/libcirrus.so --language python --out-dir .

# Second stage: Build Python environment with dependencies
FROM python:3.11.2-slim-buster as python-builder

# Set working directory for the container
WORKDIR /cirrus

# Install curl and bash utilities to build Glean
RUN apt-get update && \
    apt-get -y install curl bash build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | /bin/sh -s -- -y --no-modify-path
ENV PATH=$PATH:/root/.cargo/bin

# Install poetry package management tool
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.6.0

# Add poetry to PATH environment variable
ENV PATH "/root/.local/bin:$PATH"

# Copy only the pyproject.toml file and poetry.lock file to install dependencies ignoring dev dependencies
COPY pyproject.toml /cirrus/
COPY poetry.lock /cirrus/

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only=main --no-interaction --no-ansi

# Third stage: Deploy stage
FROM python:3.11.2-slim-buster as deploy

WORKDIR /cirrus

# Copy specific Rust components
COPY --from=rust-builder /application-services/target/release/libcirrus.so /application-services/libcirrus.so
COPY --from=rust-builder /application-services/cirrus.py /application-services/cirrus_sdk.py
COPY --from=rust-builder /application-services/fml.py /application-services/fml_sdk.py

# Copy Python site packages and scripts
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=$PYTHONPATH:/application-services

# Copy all other files into the container's working directory
COPY . .

# Start application with Uvicorn server
CMD ["uvicorn", "cirrus.main:app", "--host", "0.0.0.0", "--port", "8001"]
