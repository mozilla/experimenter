FROM rust:buster AS builder

ARG as_version

RUN rustup target add x86_64-unknown-linux-musl
RUN apt update && apt install -y musl-tools musl-dev
RUN update-ca-certificates

RUN apt-get update -qqy \
    && apt-get -qqy install \
    gyp \
    ninja-build \
    zlib1g-dev \
    tclsh \
    python3-venv

RUN git clone https://github.com/mozilla/application-services.git
RUN if [[ -z "${as_version}" ]] ; then \
    echo "No application-services version supplied, using lastest commit." \
    ; else \
    cd application-services && git fetch \
    ; fi

WORKDIR /application-services

RUN git submodule init
RUN git submodule update --recursive

RUN cargo build --manifest-path megazords/cirrus/Cargo.toml --release
RUN cargo uniffi-bindgen generate components/nimbus/src/cirrus.udl --language python

# Use official Python runtime as a parent image
FROM python:3.11.2-slim-buster

# cirrus
COPY --from=builder /application-services/components/nimbus/src/cirrus.py /application-services/cirrus_sdk.py
# megazord
COPY --from=builder /application-services/target/release/libcirrus.so /application-services/libuniffi_cirrus.so
ENV PYTHONPATH=$PYTHONPATH:/application-services

# Set working directory for the container
WORKDIR /cirrus

# Install curl and bash utilities
RUN apt-get update && \
    apt-get -y install curl bash && \
    rm -rf /var/lib/apt/lists/*

# Install poetry package management tool
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH environment variable
ENV PATH "/root/.local/bin:$PATH"

# Copy only the pyproject.toml file and poetry.lock file to install dependencies ignoring dev dependencies
COPY pyproject.toml /cirrus/pyproject.toml
COPY poetry.lock /cirrus/poetry.lock

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only=main --no-interaction --no-ansi

# Copy all other files into the container's working directory
COPY . .

# Start application with Uvicorn server
CMD ["uvicorn", "cirrus.main:app", "--host", "0.0.0.0", "--port", "8001"]
