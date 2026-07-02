# python-builder
# --------------
# This image gathers all the required Python dependencies.
FROM python:3.11-slim-bullseye AS python-builder

# Set working directory for the container
WORKDIR /cirrus

# Install curl and bash utilities to build Glean
RUN apt-get update && \
    apt-get -y install curl bash build-essential && \
    rm -rf /var/lib/apt/lists/*

# Rust is required to build some Python packages on arm64 Linux.
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | /bin/sh -s -- -y --no-modify-path
ENV PATH=$PATH:/root/.cargo/bin

# Install uv package management tool
COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /usr/local/bin/

# Copy the pyproject.toml and uv.lock files to install dependencies
COPY pyproject.toml /cirrus/
COPY uv.lock /cirrus/

# Install dependencies into a virtualenv that later stages can copy; uv has no
# global-install equivalent for this yet: https://github.com/astral-sh/uv/issues/13129
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Build glean assets
COPY ./telemetry /cirrus/telemetry
RUN glean_parser translate telemetry/pings.yaml telemetry/metrics.yaml -f python_server -o cirrus/glean

# dev image
# ---------
# The dev image contains the regular cirrus image, plus the source tree and
# developer tooling that are not suitable for a deployment.
FROM python-builder AS dev

WORKDIR /cirrus

# Copy specific Rust components
COPY --from=experimenter:megazords /application-services/megazords/cirrus/libcirrus.so /application-services/libcirrus.so
COPY --from=experimenter:megazords /application-services/megazords/cirrus/cirrus.py /application-services/cirrus_sdk.py
COPY --from=experimenter:megazords /application-services/megazords/cirrus/fml.py /application-services/fml_sdk.py

ENV PYTHONPATH=$PYTHONPATH:/application-services

# Copy fml files
COPY --from=fml . /fml/

# Copy all other files into the container's working directory
COPY . .


# deploy
# ------
# This image contains a lightweight container intended for deployment.

FROM python:3.11-slim-bullseye AS deploy

# Create a non-root user
ARG USERNAME=cirrus
ARG USER_UID=10001
ARG USER_GID=$USER_UID

# Install libatomic1 for Node.js dependencies
RUN apt-get update && \
    apt-get -y install libatomic1 && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

WORKDIR /cirrus

# Copy specific Rust components
COPY --from=experimenter:megazords /application-services/megazords/cirrus/libcirrus.so /application-services/libcirrus.so
COPY --from=experimenter:megazords /application-services/megazords/cirrus/cirrus.py /application-services/cirrus_sdk.py
COPY --from=experimenter:megazords /application-services/megazords/cirrus/fml.py /application-services/fml_sdk.py

# Copy the virtualenv and generated glean assets
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=python-builder /cirrus/cirrus/glean /cirrus/cirrus/glean

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=$PYTHONPATH:/application-services

# Copy fml files
COPY --from=fml . /fml/

# Copy all other files into the container's working directory
COPY . .

# Change ownership of the working directory to the non-root user
RUN chown -R $USERNAME:$USERNAME /cirrus

# Switch to non-root user
USER $USERNAME

# Start application with Uvicorn server
CMD ["uvicorn", "cirrus.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
