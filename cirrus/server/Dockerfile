FROM python:3.11.2-slim-buster

# Set working directory for container
WORKDIR /usr/src/cirrus

# install curl utility and bash shell
RUN apt-get update && apt-get -y install curl bash

# Install dependencies using poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "/root/.local/bin:$PATH"
COPY cirrus/server/pyproject.toml cirrus/server/poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-ansi --no-interaction \
    && rm -rf ~/.cache/pypoetry

# Copy local directory into current directory of container
COPY . .

# Start Application
CMD ["uvicorn", "cirrus.main:app", "--host", "0.0.0.0", "--port", "8001"]
