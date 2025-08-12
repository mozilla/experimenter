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

# Install poetry package management tool
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.1.1

# Add poetry to PATH environment variable
ENV PATH="/root/.local/bin:$PATH"

# Copy only the pyproject.toml file and poetry.lock file to install dependencies ignoring dev dependencies
COPY pyproject.toml /cirrus/
COPY poetry.lock /cirrus/

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only=main --no-interaction --no-ansi

# dev image
# ---------
# The dev image contains the regular cirrus image, plus additional developer
# tools (e.g., poetry) that are not suitable for a deployment.
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

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

WORKDIR /cirrus

# Copy specific Rust components
COPY --from=experimenter:megazords /application-services/megazords/cirrus/libcirrus.so /application-services/libcirrus.so
COPY --from=experimenter:megazords /application-services/megazords/cirrus/cirrus.py /application-services/cirrus_sdk.py
COPY --from=experimenter:megazords /application-services/megazords/cirrus/fml.py /application-services/fml_sdk.py

# Copy Python site packages and scripts
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=$PYTHONPATH:/application-services

# Copy fml files
COPY --from=fml . /fml/

# Copy all other files into the container's working directory
COPY . .

# Change ownership of the working directory to the non-root user
RUN chown -R $USERNAME:$USERNAME /cirrus

# Change ownership of the data directory
RUN mkdir -p /var/glean && chown -R $USERNAME:$USERNAME /var/glean

# Switch to non-root user
USER $USERNAME

# Start application with Uvicorn server
CMD ["uvicorn", "cirrus.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
