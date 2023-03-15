# Use official Python runtime as a parent image
FROM python:3.11.2-slim-buster

# Set working directory for the container
WORKDIR /app/cirrus

# Install curl and bash utilities
RUN apt-get update && \
    apt-get -y install curl bash && \
    rm -rf /var/lib/apt/lists/*

# Install poetry package management tool
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH environment variable
ENV PATH "/root/.local/bin:$PATH"

# Copy only the pyproject.toml file and poetry.lock file to install dependencies ignoring dev dependencies
COPY cirrus/server/pyproject.toml cirrus/server/poetry.lock ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only=main --no-interaction --no-ansi

# Copy all other files into the container's working directory
COPY . .

# Start application with Uvicorn server
CMD ["uvicorn", "cirrus.main:app", "--host", "0.0.0.0", "--port", "8001"]
