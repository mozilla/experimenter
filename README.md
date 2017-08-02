# ![Logo](https://raw.githubusercontent.com/mozilla/experimenter/22/app/experimenter/static/imgs/favicon_24.png) Experimenter 

[![CircleCI](https://circleci.com/gh/mozilla/experimenter.svg?style=svg)](https://circleci.com/gh/mozilla/experimenter)

Experimenter is a Python/Django application for managing experiments in Mozilla projects, such as [Activity Stream](https://github.com/mozilla/activity-stream).

### What is an experiment?

An experiment is a way to measure how a change to an application will affect its usage and behaviour. For example
you could change the way your application processes data in a way that affects its performance characteristics, as well
as how it presents that data to the user.  To make that change into an experiment, you could create a flag which optionally
enables the new code path, and then enable it for a subset of users and measure how it affects things like performance and
engagement.

## Installation

1) Install [docker](https://www.docker.com/) on your machine 

1) Clone the repo

        git clone <your fork>

1) Copy the sample env file

        cp .env.sample .env

1) Create a new secret key and put it in .env

        make secretkey

1) Run tests

        make test

1) Run database migrations

        make migrate

1) Make a local user

        make createuser

1) Run a dev instance

        make up
Done!

## Usage

Experimenter uses [docker](https://www.docker.com/) for all development, testing, and deployment.  

The following helpful commands have been provided via a Makefile:

### build
Build the application container by executing the [build script](https://github.com/mozilla/experimenter/blob/master/scripts/build.sh)

### compose_build
Build the supporting services (nginx, postgresql) defined in the [compose file](https://github.com/mozilla/experimenter/blob/master/docker-compose.yml)

### up
Start a dev server listening on port 80 using the [Django runserver](https://docs.djangoproject.com/en/1.10/ref/django-admin/#runserver)

### test
Run the Django test suite with code coverage

### lint
Run flake8 against the code

### check
Run both test and lint

### migrate
Apply all django migrations

### createuser
Create an admin user in the local dev instance

### shell
Start an ipython shell inside the container (this lets you import and test code, interact with the db, etc)

### bash
Start a bash shell inside the container (this lets you interact with the containerized filesystem)

## API

### GET /api/v1/experiments/
List all of the started experiments.

#### Optional Query Parameters
project__slug - Return only the experiments for a given project, an invalid slug will raise 404

Example: GET /api/v1/experiments/?project__slug=project-slug

        [
          {
            "active": true,
            "name": "New Feature",
            "slug": "new-feature",
            "pref_key": "new.feature",
            "addon_versions": [
              "1.0",
              "2.0"
            ],
            "start_date": 1493928948000.0,
            "end_date": 1495138548000.0,
            "variant": {
              "slug": "enabled",
              "experiment_variant_slug": "new-feature:enabled",
              "value": true,
              "threshold": 0.2
            },
            "control": {
              "slug": "disabled",
              "experiment_variant_slug": "new-feature:disabled",
              "value": false
            }
          }
        ]

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D


## License

Experimenter uses the [Mozilla Public License](https://www.mozilla.org/en-US/MPL/)
