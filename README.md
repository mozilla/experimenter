# Mozilla Experimenter

[![CircleCI](https://circleci.com/gh/mozilla/experimenter.svg?style=svg)](https://circleci.com/gh/mozilla/experimenter) ![Status](https://img.shields.io/badge/Status-Invest-green)

Experimenter is a platform for managing experiments in [Mozilla Firefox](https://www.mozilla.org/en-US/firefox/?utm_medium=referral&utm_source=firefox-com).

## Important Links

Check out the [🌩 **Nimbus Documentation Hub**](https://experimenter.info) or go to [the repository](https://github.com/mozilla/experimenter-docs/) that house those docs.

| Link            | Prod                                                  | Staging                                                            | Local Dev (Default)                           |
| --------------- | ----------------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| Legacy Home     | [experimenter.services.mozilla.com][legacy_home_prod] | [stage.experimenter.nonprod.dataops.mozgcp.net][legacy_home_stage] | https://localhost                             |
| Nimbus Home     | [/nimbus][nimbus_home_prod]                           | [/nimbus][nimbus_home_stage]                                       | [/nimbus][nimbus_home_local]                  |
| Nimbus REST API | [/api/v6/experiments/][nimbus_rest_api_prod]          | [/api/v6/experiments/][nimbus_rest_api_stage]                      | [/api/v6/experiments/][nimbus_rest_api_local] |
| GQL Playground  | [/api/v5/nimbus-api-graphql][gql_prod]                | [/api/v5/nimbus-api-graphql][gql_stage]                            | [/api/v5/nimbus-api-graphql][gql_local]       |
| Remote Settings | [remote-settings.mozilla.org/v1/admin][rs_prod]       | [remote-settings.allizom.org/v1/admin][rs_stage]                   | http://localhost:8888/v1/admin                |

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
[rs_prod]: https://remote-settings.mozilla.org/v1/admin/
[rs_stage]: https://remote-settings.allizom.org/v1/admin/

## Installation

### General Setup

1.  Prerequisites

    On all platforms:

    - Install [Node](https://nodejs.org/en/download/releases/) to match [current version](https://github.com/mozilla/experimenter/blob/main/experimenter/Dockerfile#L29)

    On Linux:

    - Install [Docker](https://www.docker.com/)
    - Install [yarn](https://classic.yarnpkg.com/lang/en/docs/install)
    - [Setup docker to run as non-root](https://docs.docker.com/engine/security/rootless/)

    On MacOS:

    - Install [Docker](https://docs.docker.com/desktop/mac/install/)
      - Adjust resource settings
        - CPU: Max number of cores
        - Memory: 50% of system memory
        - Swap: Max 4gb
        - Disk: 100gb+
    - Install [yarn](https://github.com/yarnpkg)

    On Windows:

    - Install WSL on Windows
        - Download from Microsoft store. Or
        - Download within Powershell.

                Open PowerShell as administrator.
                Run `wsl --install` to install wsl.
                Run `wsl --list --online` to see list of available Ubuntu distributions.
                Run `wsl --install -d <distroname>` to install a particular distribution e.g `wsl --install -d Ubuntu-22.04`.

        - After installation, press Windows Key and search for Ubuntu. Open it and set up username and password.
    - Download and Install [Docker](https://docs.docker.com/desktop/install/windows-install/)
        - Restart System after Installation.
        - Open Docker and go to settings.
        - Go to settings -> Resources -> WSL Integration and activate Ubuntu.
        - Click the activate and restart button to save your change.
    - Install Make and Git
        - Open the ubuntu terminal
        - You should install make using this command `sudo apt-get update && sudo apt install make` in the ubuntu terminal.
        This is necessary for the `make secretkey` command and other commands.
        - Ensure git is available by running `git --version`. If it's not recognized, install git using `sudo apt install git`

1.  Clone the repo

        git clone <your fork>

1.  Copy the sample env file

        cp .env.sample .env

1.  Set DEBUG=True for local development

        vi .env

1.  Create a new secret key and put it in .env

        make secretkey

    vi .env

    ```
    ...
    SECRETKEY=mynewsecretkey
    ...
    ```

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
1. better IDE integration

Notes:

- [osx catalina, reinstall command line tools](https://medium.com/flawless-app-stories/gyp-no-xcode-or-clt-version-detected-macos-catalina-anansewaa-38b536389e8d)

- Install [poetry](https://python-poetry.org/docs/#installation)

##### Semi Dockerized Setup Steps

1.  Pre reqs
    macOS instructions:

        brew install postgresql llvm openssl yarn

        echo 'export PATH="/usr/local/opt/llvm/bin:$PATH"' >> ~/.bash_profile
        export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/opt/openssl/lib/

    Ubuntu 20.04 instructions:

        # general deps (also see `poetry` link above)
        sudo apt install postgresql llvm openssl yarn

        # add'l deps* for poetry / python setup
        sudo apt install libpq5=12.9-0ubuntu0.20.04.1
        sudo apt install libpq-dev

    _\*Notes_

    - _the specific libpq5 version shown here is required for libpq-dev at time of writing_
    - _`poetry install` (next step) requires python 3.9, but there are multiple options for resolving this, see [here](https://python-poetry.org/docs/managing-environments/#switching-between-environments)_

2.  Install dependencies

        source .env

        cd experimenter
        poetry install # see note above

        yarn install

3.  env values

        .env (set at root):
        DEBUG=True
        DB_HOST=localhost
        HOSTNAME=localhost

4.  Start postgresql, redis, autograph, kinto

        make up_db (from project root)

5.  Django app

        # in experimenter

        poetry shell

        yarn workspace @experimenter/nimbus-ui build
        yarn workspace @experimenter/core build

        # run in separate shells (`poetry shell` in each)
        yarn workspace @experimenter/nimbus-ui start
        ./manage.py runserver 0.0.0.0:7001

_Pro-tip_: we have had at least one large code refactor. You can ignore specific large commits when blaming by setting the Git config's `ignoreRevsFile` to `.git-blame-ignore-revs`:

```
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

### VSCode setup

1. If using VSCode, configure workspace folders

   - Add `/experimenter/` and `/experimenter/experimenter` folders to your workspace (File -> Add Folder to Workspace -> `path/to/experimenter/experimenter`)
   - From the `/experimenter/experimenter` folder, run `yarn install`

     - Make sure you are using the correct version of node

       node -v

     - Troubleshooting:
       - [Changing node version](https://stackoverflow.com/a/50817276/12178648)
       - Clear npm cache: `npm cache clean --force`

### Google Credentials for Jetstream

On certain pages an API endpoint is called to receive experiment analysis data from Jetstream to display visualization tables. To see experiment visualization data, you must provide GCP credentials.

0. Prequisites

   - Install GCP CLI
     - Follow the instructions [here](https://cloud.google.com/sdk/docs/install)
     - Project: `moz-fx-data-experiments`
   - Verify/request project permissions
     - Check if you already have access to the storage bucket [here](https://console.cloud.google.com/storage/browser/mozanalysis)
     - If needed, ask in `#nimbus-dev` for a project admin to grant `storage.objects.list` permissions on the `moz-fx-data-experiments` project

1. Authorize CLI with your account

   - `make auth_gcloud`
     - this will save your credentials locally to a well-known location for use by any library that requests ADC
     - **Note**: if this returns `Error saving Application Default Credentials: Unable to write file [...]: [Errno 21] Is a directory: ...`, delete the directory and try again (`rm -rf ~/.config/gcloud`)

2. The next time you rebuild the docker-compose environment, your credentials will be loaded as a volume

   - Note that this will require the existing volume to be removed (hint: run `make refresh`)

3. (optional) Verify access
   - `make refresh`
   - `make bash`
   - `./manage.py shell`
     - ```
       from django.core.files.storage import default_storage
       default_storage.listdir('/')
       ```
     - Confirm this second command prints a list instead of an error

### Google Cloud Bucket for Media Storage

We support user uploads of media (e.g. screenshots) for some features.

In local development, the default is to store these files in `/experimenter/media` using Django's `FileSystemStorage` class and the `MEDIA_ROOT` and `MEDIA_URL` settings.

In production, a GCP bucket and credentials are required.

The bucket name is configured with the `UPLOADS_GS_BUCKET_NAME` setting. For example:

```
UPLOADS_GS_BUCKET_NAME=nimbus-experimenter-media-dev-uploads
```

For local testing of a production-like environment, The credentials should be configured as described in the previous section on Google Credentials for Jetstream.

In the real production deployment, credentials are configured via [workload identity in Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity).

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

Apply all django migrations to the database. This must be run after removing database volumes before starting a dev instance.

#### make load_dummy_experiments

Populates the database with dummy experiments of all types/statuses using the test factories

#### make refresh

Run kill, migrate, load_locales_countries load_dummy_experiments. Useful for resetting your dev environment when switching branches or after package updates.

### Running a dev instance

#### Enabling Cirrus

Cirrus is required to run and test web application experiments locally.  It is disabled by default.  To enable Cirrus run:

```sh
export CIRRUS=1
```

This will be done automatically for any Cirrus related make commands.

#### make up

Start a dev server listening on port 80 using the [Django runserver](https://docs.djangoproject.com/en/1.10/ref/django-admin/#runserver). It is useful to run `make refresh` first to ensure your database is up to date with the latest migrations and test data.

#### make up_db

Start postgresql, redis, autograph, kinto on their respective ports to allow running the Django runserver and yarn watchers locally (non containerized)

#### make up_django

Start Django runserver, Celery worker, postgresql, redis, autograph, kinto on their respective ports to allow running the yarn watchers locally (non containerized)

#### make up_detached

Start all containers in the background (not attached to shell). They can be stopped using `make kill`.

#### make update_kinto

Pull in the latest Kinto Docker image. Kinto is not automatically updated when new versions are available, so this command can be used occasionally to stay in sync.

### Running tests and checks

#### make check

Run all test and lint suites, this is run in CI on all PRs and deploys.

##### Helpful UI Testing Tips

If you have a test failing to find an element (or finding too many, etc.) and the DOM is being cut off in the console output,
you can increase how much is printed by locally editing the `DEBUG_PRINT_LIMIT=7000` in the `Makefile` (line starts with `JS_TEST_NIMBUS_UI`).

#### make py_test

Run only the python test suite.

#### make bash

Start a bash shell inside the container. This lets you interact with the containerized filesystem and run Django management commands.

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

#### make integration_test_legacy

Run the integration test suite for experimenter inside a containerized instance of Firefox. You must also be already running a `make up` dev instance in another shell to run the integration tests.

#### make FIREFOX_VERSION integration_test_nimbus

Run the integration test suite for nimbus inside a containerized instance of Firefox. You must also be already running a `make up` dev instance in another shell to run the integration tests.

FIREFOX_VERSION should either be `nimbus-firefox-release` or `nimbus-firefox-beta`. If you want to run your tests against nightly, please set the variable `UPDATE_FIREFOX_VERSION` to `true` and include it in the make command.

#### make FIREFOX_VERSION integration_vnc_up

First start a prod instance of Experimenter with:

```bash
make refresh&&make up_prod_detached
```

Then start the VNC service:

```bash
make FIREFOX_VERSION integration_vnc_up
```

Then open your VNC client (Safari does this on OSX or just use [VNC Viewer](https://www.realvnc.com/en/connect/download/viewer/)) and open `vnc://localhost:5900` with password `secret`. Right click on the desktop and select `Applications > Shell > Bash` and enter:

```bash
cd experimenter
sudo apt get update
sudo apt install tox
chmod a+rwx tests/integration/.tox
tox -c tests/integration/ -e integration-test-nimbus
```

This should run the integration tests and watch them run in a Firefox instance you can watch and interact with.

To use NoVNC, navgate to this url `http://localhost:7902` with the password `secret`. Then you can follow the same steps as above.

#### Integration Test options

- `TOX_ARGS`: [Tox](https://tox.readthedocs.io/en/latest/config.html#tox) commandline variables.
- `PYTEST_ARGS`: [Pytest](https://docs.pytest.org/en/6.2.x/usage.html#) commandline variables.

An example using PYTEST_ARGS to run one test.

```bash
make integration_test_legacy PYTEST_ARGS="-k test_addon_rollout_experiment_e2e"
```

Note: You need the following firefox version flag when running integration tests

```sh
FIREFOX_VERSION=nimbus-firefox-release
```

An example for above:

```sh
make FIREFOX_VERSION=nimbus-firefox-release integration_test_nimbus PYTEST_ARGS=ktest_rollout_create_and_update
```

#### make integration_sdk_shell

This builds and sets up the mobile sdk for use in testing.

### Testing Tools

#### Targeting test tool

Navigate to `experimenter/tests/tools`

To test a targeting expression, first add an app context named `app_context.json` to the `experimenter/tests/tools` directory.

You can then invoke the script with the `--targeting-string` flag:

```bash
python sdk_eval_check.py --targeting-string "(app_version|versionCompare('106.*') <= 0) && (is_already_enrolled)"
```

The script should return the results, either `True`, `False`, or an error.

Note that you can change the `app_context` live, and run the script again after.

## Accessing Remote Settings locally

In development you may wish to approve or reject changes to experiments as if they were on Remote Settings. You can do so here: `http://localhost:8888/v1/admin/`

There are three accounts you can log into Kinto with depending on what you want to do:

- `admin` / `admin` - This account has permission to view and edit all of the collections.
- `experimenter` / `experimenter` - This account is used by Experimenter to push its changes to Remote Settings and mark them for review.
- `review` / `review` - This account should generally be used by developers testing the workflow, it can be used to approve/reject changes pushed from Experimenter.

The `admin` and `review` credentials are hard-coded [here](https://github.com/mozilla/experimenter/blob/main/experimenter/bin/setup_kinto.py#L7-L8), and the `experimenter` credentials can be found or updated in your `.env` file under `KINTO_USER` and `KINTO_PASS`.

Any change in remote settings requires two accounts:

- One to make changes and request a review
- One to review and approve/reject those changes

Any of the accounts above can be used for any of those two roles, but your local Experimenter will be configured to make its changes through the `experimenter` account, so that account can't also be used to approve/reject those changes, hence the existence of the `review` account.

For more detailed information on the Remote Settings integration please see the [Kinto module documentation](experimenter/experimenter/kinto/README.md).

## Frontend

Experimenter has two front-end UIs:

- [`core`](./experimenter/experimenter/legacy/legacy-ui/core) is the legacy UI used for Experimenter intake which will remain until `nimbus-ui` supersedes it
- [`nimbus-ui`](./experimenter/experimenter/nimbus-ui) is the Nimbus Console UI for Experimenter that is actively being developed

Learn more about the organization of these UIs [here](./experimenter/experimenter/legacy/legacy-ui/README.md).

**Also see the [nimbus-ui README](https://github.com/mozilla/experimenter/tree/main/experimenter/experimenter/nimbus-ui) for relevent Nimbus documentation.**

## API

API documentation can be found [here](https://htmlpreview.github.io/?https://github.com/mozilla/experimenter/blob/main/docs/experimenter/swagger-ui.html)

## Contributing

Please see our [Contributing Guidelines](https://github.com/mozilla/experimenter/blob/main/contributing.md)

## License

Experimenter uses the [Mozilla Public License](https://www.mozilla.org/en-US/MPL/)
