# First stage: Build the Rust components
FROM rust:buster AS rust-builder

ARG as_version

RUN update-ca-certificates

RUN apt-get update -qqy \
    && apt-get -qqy install \
    gyp \
    ninja-build \
    zlib1g-dev \
    tclsh \
    python3-venv

WORKDIR /application-services

RUN git clone https://github.com/mozilla/application-services.git .
RUN if [[ -z "${as_version}" ]] ; then \
    echo "No application-services version supplied, using the latest commit." ; \
    else \
    git fetch ; \
    fi

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
RUN curl -sSL https://install.python-poetry.org | python3 -

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

WORKDIR /app

# Copy specific Rust components
COPY --from=rust-builder /application-services/target/release/libcirrus.so /application-services/libcirrus.so
COPY --from=rust-builder /application-services/cirrus.py /application-services/cirrus_sdk.py
COPY --from=rust-builder /application-services/fml.py /application-services/fml_sdk.py

# Copy Python site packages and scripts
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Set environment variables
ENV PYTHONPATH=$PYTHONPATH:/application-services
ENV PORT=8001

# Create an app group with GID of 10001
RUN groupadd -g 10001 app

# Create an app user with UID of 10001 and make them a member of the app group
RUN useradd -u 10001 -g 10001 -m -s /bin/sh app

RUN chown -R app:app /app

# Set the user to "app" and accept configuration through environment variables
USER app

# Copy all other files into the container's working directory (/app)
COPY  . /app

# Start application with Uvicorn server
CMD ["sh", "-c", "uvicorn cirrus.main:app --host 0.0.0.0 --port $PORT"]
