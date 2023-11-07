# First stage: Build Python environment with dependencies
FROM python:3.11.2-slim-bullseye as python-builder

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

# Second stage: Deploy stage
FROM python:3.11.2-slim-bullseye as deploy

WORKDIR /cirrus

# Copy cirrus megazord
COPY --from=as-builder /application-services/cirrus/ /application-services/

# Copy Python site packages and scripts
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=$PYTHONPATH:/application-services

# Copy all other files into the container's working directory
COPY . .

# Start application with Uvicorn server
CMD ["uvicorn", "cirrus.main:app", "--host", "0.0.0.0", "--port", "8001"]
