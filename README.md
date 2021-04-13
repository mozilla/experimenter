# Mozilla Experimenter

[![CircleCI](https://circleci.com/gh/mozilla/experimenter.svg?style=svg)](https://circleci.com/gh/mozilla/experimenter)

Experimenter is a platform for managing experiments in [Mozilla Firefox](https://www.mozilla.org/en-US/firefox/?utm_medium=referral&utm_source=firefox-com).

## Important Links

Check out the [🌩 **Nimbus Documentation Hub**](https://mozilla.github.io/experimenter-docs/) or go to [the repository](https://github.com/mozilla/experimenter-docs/) that house those docs.

| Link            | Prod                                                  | Staging                                                            | Local Dev (Default)                           |
| --------------- | ----------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| Legacy Home     | [experimenter.services.mozilla.com][legacy_home_prod] | [stage.experimenter.nonprod.dataops.mozgcp.net][legacy_home_stage] | https://localhost                             |
| Nimbus Home     | [/nimbus][nimbus_home_prod]                           | [/nimbus][nimbus_home_stage]                                       | [/nimbus][nimbus_home_local]                  |
| Nimbus REST API | [/api/v6/experiments/][nimbus_rest_api_prod]          | [/api/v6/experiments/][nimbus_rest_api_stage]                      | [/api/v6/experiments/][nimbus_rest_api_local] |
| GQL Playground  | [/api/v5/nimbus-api-graphql][gql_prod]                | [/api/v5/nimbus-api-graphql][gql_stage]                            | [/api/v5/nimbus-api-graphql][gql_local]       |
| Storybook       | [Storybook Directory][storybook_prod]                 |                                                                    | https://localhost:3001                        |
| Remote Settings | [settings-writer.prod.mozaws.net/v1/admin][rs_prod]   | [settings-writer.stage.mozaws.net/v1/admin][rs_stage]              | http://localhost:8888/v1/admin                |

[legacy_home_prod]: https://experimenter.services.mozilla.com/
[legacy_home_stage]: https://stage.experimenter.nonprod.dataops.mozgcp.net/
[nimbus_home_prod]: https://experimenter.services.mozilla.com/nimbus
[nimbus_home_stage]: https://stage.experimenter.nonprod.dataops.mozgcp.net/nimbus
[nimbus_home_local]: https://localhost/nimbus
[nimbus_rest_api_prod]: https://experimenter.services.mozilla.com/api/v6/experiments/
[nimbus_rest_api_stage]: https://stage.experimenter.nonprod.dataops.mozgcp.net/api/v6/experiments/
[nimbus_rest_api_local]: https://localhost/api/v6/experiments/
[gql_prod]: https://experimenter.services.mozilla.com/api/v5/nimbus-api-graphql/
[gql_stage]: https://stage.experimenter.nonprod.dataops.mozgcp.net/api/v5/nimbus-api-graphql/
[gql_local]: https://localhost/api/v5/nimbus-api-graphql/
[storybook_prod]: https://storage.googleapis.com/mozilla-storybooks-experimenter/index.html
[rs_prod]: https://settings-writer.prod.mozaws.net/v1/admin/
[rs_stage]: https://settings-writer.stage.mozaws.net/v1/admin/

## Installation

### General Setup

1.  Install [docker](https://www.docker.com/) on your machine

- On linux, [setup docker to run as non-root](https://docs.docker.com/engine/security/rootless/)

1.  Clone the repo

        git clone <your fork>

1.  Copy the sample env file

        cp .env.sample .env

1.  Set DEBUG=True for local development

        vi .env

1.  Create a new secret key and put it in .env

        make secretkey

1.  Run tests

        make check

1.  Setup the database

        make refresh

#### Fully Dockerized Setup (continuation from General Setup 1-7)

1.  Run a dev instance

        make up

1.  Navigate to it and add an SSL exception to your browser

        https://localhost/

#### Semi Dockerized Setup (continuation from General Setup 1-7)

One might choose the semi dockerized approach for:

1. faster startup/teardown time (not having to rebuild/start/stop containers)
1. better ide integration

Notes:

- Node ^14.0.0 is required

- [osx catalina, reinstall command line tools](https://medium.com/flawless-app-stories/gyp-no-xcode-or-clt-version-detected-macos-catalina-anansewaa-38b536389e8d)

- [poetry](https://python-poetry.org/docs/#installation)

### Semi Dockerized Setup

1.  Pre reqs (macOs instructions)

        brew install postgresql llvm openssl yarn

        echo 'export PATH="/usr/local/opt/llvm/bin:$PATH"' >> ~/.bash_profile
        export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/opt/openssl/lib/

2.  Install dependencies

        source .env

        poetry install (cd into app)

        yarn install

3.  env values

        .env (set at root):
        DEBUG=True
        DB_HOST=localhost
        HOSTNAME=localhost

4.  Start postgresql, redis, autograph, kinto

        make up_db

5.  Django app

        # in app

        poetry shell

        yarn workspace @experimenter/nimbus-ui build
        yarn workspace @experimenter/core build
        ./manage.py runserver 0.0.0.0:7001

Pro-tip: we have had at least one large code refactor. You can ignore specific large commits when blaming by setting the Git config's `ignoreRevsFile` to `.git-blame-ignore-revs`:

```
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

### Google Credentials

On certain pages an API endpoint is called to receive experiment analysis data from Jetstream to display visualization tables. To see experiment visualization data, you must provide GCP credentials.

1. Generate a GCP private key file.

- Ask in #experimenter for the GCP link to create a new key file.
- Add Key > Create New Key > JSON > save this file.
- Do not lose or share this file. It's unique to you and you'll only get it once.

2. Rename the file to `google-credentials.json` and place it anywhere inside the `/app` directory.
3. Update your `.env` so that `GOOGLE_APPLICATION_CREDENTIALS` points to this file. If your file is inside the `/app` directory it would look like this:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json
   ```

## Usage

Experimenter uses [docker](https://www.docker.com/) for all development, testing, and deployment.

### Building
#### make build

Build the application container by executing the [build script](https://github.com/mozilla/experimenter/blob/main/scripts/build.sh)

#### make compose_build

Build the supporting services (nginx, postgresql) defined in the [compose file](https://github.com/mozilla/experimenter/blob/main/docker-compose.yml)

#### make ssl

Create dummy SSL certs to use the dev server over a locally secure
connection. This helps test client behaviour with a secure
connection. This task is run automatically when needed.

#### make kill

Stop and delete all docker containers.
WARNING: this will remove your database and all data. Use this to reset your dev environment.

#### make migrate

Apply all django migrations to the database.  This must be run after removing database volumes before starting a dev instance.

#### make load_locales_countries

Populates locales and countries in the database from the [Firefox Product Details package](https://pypi.org/project/django-mozilla-product-details/)

#### make load_dummy_experiments

Populates the database with dummy experiments of all types/statuses using the test factories

#### make refresh

Run kill, migrate, load_locales_countries load_dummy_experiments.  Useful for resetting your dev environment when switching branches or after package updates.

### Running a dev instance
#### make up

Start a dev server listening on port 80 using the [Django runserver](https://docs.djangoproject.com/en/1.10/ref/django-admin/#runserver).  It is useful to run `make refresh` first to ensure your database is up to date with the latest migrations and test data.

#### make up_db

Start postgresql, redis, autograph, kinto on their respective ports to allow running the Django runserver and yarn watchers locally (non containerized)

#### make up_django

Start Django runserver, Celery worker, postgresql, redis, autograph, kinto on their respective ports to allow running the yarn watchers locally (non containerized)

#### make up_detached

Start all containers in the background (not attached to shell).  They can be stopped using `make kill`.

### Running tests and checks

#### make check

Run all test and lint suites, this is run in CI on all PRs and deploys.

#### make py_test

Run only the python test suite.

#### make bash

Start a bash shell inside the container.  This lets you interact with the containerized filesystem and run Django management commands.

##### Helpful Python Tips
You can run the entire python test suite without coverage using the Django test runner:

```sh
./manage.py test
```

For faster performance you can run all tests in parallel:

```sh
./manage.py test --parallel
```

You can run only the tests in a certain module by specifying its Python import path:

```sh
./manage.py test experimenter.experiments.tests.api.v5.test_serializers
```

For more details on running Django tests refer to the [Django test documentation](https://docs.djangoproject.com/en/3.1/topics/testing/overview/#running-tests)

To debug a test, you can use ipdb by placing this snippet anywhere in your code, such as within a test method or inside some application logic:

```py
import ipdb
ipdb.set_trace()
```

Then invoke the test using its full path:

```sh
./manage.py test experimenter.some_module.tests.some_test_file.SomeTestClass.test_some_thing
```

And you will enter an interactive iPython shell at the point where you placed the ipdb snippet, allowing you to introspect variables and call methods

For coverage you can use pytest, which will run all the python tests and track their coverage, but it is slower than using the Django test runner:

```sh
pytest --cov --cov-report term-missing
```

You can also enter a Python shell to import and interact with code directly, for example:

```sh
./manage.py shell
```

And then you can import and execute arbitrary code:

```py
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.kinto.tasks import nimbus_push_experiment_to_kinto

experiment = NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.DRAFT, name="Look at me, I'm Mr Experiment")
nimbus_push_experiment_to_kinto(experiment.id)
```

##### Helpful Yarn Tips
You can also interact with the yarn commands, such as checking TypeScript for Nimbus UI:

```sh
yarn workspace @experimenter/nimbus-ui lint:tsc
```

Or the test suite for Nimbus UI:

```sh
yarn workspace @experimenter/nimbus-ui test:cov
```

For a full reference of all the common commands that can be run inside the container, refer to [this section of the Makefile](https://github.com/mozilla/experimenter/blob/main/Makefile#L16-L38)




#### make integration_test

Run the integration test suite inside a containerized instance of Firefox. You must also be already running a `make up` dev instance in another shell to run the integration tests.

#### make integration_vnc_up

Start a linux VM container with VNC available over `vnc://localhost:5900` with password `secret`. Right click on the desktop and select `Applications > Shell > Bash` and enter `tox -c tests/integration/` to run the integration tests and watch them run in a Firefox instance you can watch and interact with.

## Accessing Remote Settings locally

In development you may wish to approve or reject changes to experiments as if they were on Remote Settings. You can do so here: `http://localhost:8888/v1/admin/`

There are three accounts you can log into Kinto with depending on what you want to do:

- `admin` / `admin` - This account has permission to view and edit all of the collections.
- `experimenter` / `experimenter` - This account is used by Experimenter to push its changes to Remote Settings and mark them for review.
- `review` / `review` - This account should generally be used by developers testing the workflow, it can be used to approve/reject changes pushed from Experimenter.

The `admin` and `review` credentials are hard-coded [here](https://github.com/mozilla/experimenter/blob/main/app/bin/setup_kinto.py#L7-L8), and the `experimenter` credentials can be found or updated in your `.env` file under `KINTO_USER` and `KINTO_PASS`.

Any change in remote settings requires two accounts:

- One to make changes and request a review
- One to review and approve/reject those changes

Any of the accounts above can be used for any of those two roles, but your local Experimenter will be configured to make its changes through the `experimenter` account, so that account can't also be used to approve/reject those changes, hence the existence of the `review` account.

For more detailed information on the Remote Settings integration please see the [Kinto module documentation](app/experimenter/kinto/README.md).

## Frontend

Experimenter has two front-end UIs:

- [`core`](./app/experimenter/legacy-ui/core) is the legacy UI used for Experimenter intake which will remain until `nimbus-ui` supersedes it
- [`nimbus-ui`](./app/experimenter/nimbus-ui) is the Nimbus Console UI for Experimenter that is actively being developed

Learn more about the organization of these UIs [here](./app/experimenter/legacy-ui/README.md).

**Also see the [nimbus-ui README](https://github.com/mozilla/experimenter/tree/main/app/experimenter/nimbus-ui) for relevent Nimbus documentation.**

## API

API documentation can be found [here](https://htmlpreview.github.io/?https://github.com/mozilla/experimenter/blob/main/app/experimenter/docs/swagger-ui.html)

## Contributing

Please see our [Contributing Guidelines](https://github.com/mozilla/experimenter/blob/main/contributing.md)

## License

Experimenter uses the [Mozilla Public License](https://www.mozilla.org/en-US/MPL/)
