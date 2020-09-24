# Mozilla Experimenter

[![CircleCI](https://circleci.com/gh/mozilla/experimenter.svg?style=svg)](https://circleci.com/gh/mozilla/experimenter)

<p align="center">
  <img src="https://cdn1.iconfinder.com/data/icons/simple-arrow/512/arrow_20-128.png"><br/>
  <b>1. Design 2. Launch 3. Analyze</b>
  <br><br>
</p>

Experimenter is a platform for managing experiments in [Mozilla Firefox](https://www.mozilla.org/en-US/firefox/?utm_medium=referral&utm_source=firefox-com).

## Deployments

### Staging

<https://stage.experimenter.nonprod.dataops.mozgcp.net/>

### Production

<https://experimenter.services.mozilla.com/>


## Installation
### Fully Dockerized Dev Environment

1.  Install [docker](https://www.docker.com/) on your machine

1.  Clone the repo

        git clone <your fork>

1.  Copy the sample env file

        cp .env.sample .env

1.  Set DEBUG=True for local development

        vi .env

1.  Create a new secret key and put it in .env

        make secretkey

1.  Run tests

        make test

1.  Setup the database

        make refresh

1.  Run a dev instance

        make up

1.  Navigate to it and add an SSL exception to your browser

        https://localhost/

Done!

Pro-tip: we have had at least one large code refactor. You can ignore specific large commits when blaming by setting the Git config's `ignoreRevsFile` to `.git-blame-ignore-revs`:

```
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

## Usage

Experimenter uses [docker](https://www.docker.com/) for all development, testing, and deployment.

The following helpful commands have been provided via a Makefile:

### build

Build the application container by executing the [build script](https://github.com/mozilla/experimenter/blob/main/scripts/build.sh)

### compose_build

Build the supporting services (nginx, postgresql) defined in the [compose file](https://github.com/mozilla/experimenter/blob/main/docker-compose.yml)

### up

Start a dev server listening on port 80 using the [Django runserver](https://docs.djangoproject.com/en/1.10/ref/django-admin/#runserver)

### up_db

Start postgresql, redis, autograph, kinto on their respective ports to allow running the Django runserver and yarn watchers locally (non containerized)

### up_django

Start Django runserver, Celery worker, postgresql, redis, autograph, kinto on their respective ports to allow running the yarn watchers locally (non containerized)

### up_detached

Start all containers in the background (not attached to shell)

### check

Run all test and lint suites, this is run in CI on all PRs and deploys

### migrate

Apply all django migrations

### load_locales_countries

Populates locales and countries

### load_dummy_experiments

Populates db with dummy experiments

### bash

Start a bash shell inside the container (this lets you interact with the containerized filesystem and run Django management commands)

### ssl

Create dummy SSL certs to use the dev server over a locally secure
connection. This helps test client behaviour with a secure
connection. This task is run automatically when needed.

### kill

Stop and delete all docker containers.
WARNING: this will remove your database and all data. Use this to reset your dev environment.

### refresh

Run kill, migrate, load_locales_countries load_dummy_experiments

### integration_test

Run the integration test suite inside a containerized instance of Firefox. You must also be already running a `make up` dev instance in another shell to run the integration tests.

### integration_vnc_up

Start a linux VM container with VNC available over `vnc://localhost:5900` with password `secret`. Right click on the desktop and select `Applications > Shell > Bash` and enter `tox -c tests/integration/` to run the integration tests and watch them run in a Firefox instance you can watch and interact with.

## Frontend

Experimenter has three front-end UIs right now:

- [`core`](./app/experimenter/legacy-ui/core) is the current UI used for Experimenter intake.
- [`rapid`](./app/experimenter/legacy-ui/core) is a partially-built React UI.
- [`nimbus-ui`](./app/experimenter/nimbus-ui) is a new React UI for an upcoming Experimenter refactor.

Learn more about the organization of these UIs [here](./app/experimenter/legacy-ui/README.md).

## API

API documentation can be found [here](https://htmlpreview.github.io/?https://github.com/mozilla/experimenter/blob/main/app/experimenter/docs/swagger-ui.html)

## Contributing

Please see our [Contributing Guidelines](https://github.com/mozilla/experimenter/blob/main/contributing.md)

## License

Experimenter uses the [Mozilla Public License](https://www.mozilla.org/en-US/MPL/)
