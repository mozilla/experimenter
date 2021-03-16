# Mozilla Experimenter

[![CircleCI](https://circleci.com/gh/mozilla/experimenter.svg?style=svg)](https://circleci.com/gh/mozilla/experimenter)

Experimenter is a platform for managing experiments in [Mozilla Firefox](https://www.mozilla.org/en-US/firefox/?utm_medium=referral&utm_source=firefox-com).

## Important Links

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

### py_test

Run python tests

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
