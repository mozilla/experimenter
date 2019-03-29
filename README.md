# Mozilla Experimenter

[![CircleCI](https://circleci.com/gh/mozilla/experimenter.svg?style=svg)](https://circleci.com/gh/mozilla/experimenter)
[![What's deployed on dev,stage,prod?](https://img.shields.io/badge/whatsdeployed-dev,stage,prod-green.svg)](https://whatsdeployed.io/s/uFe)

<p align="center">
  <img src="https://cdn1.iconfinder.com/data/icons/simple-arrow/512/arrow_20-128.png"><br/>
  <b>1. Design 2. Launch 3. Analyze</b>
  <br><br>
</p>

Experimenter is a platform for managing experiments in [Mozilla Firefox](https://www.mozilla.org/en-US/firefox/?utm_medium=referral&utm_source=firefox-com).

## Deployments

### Shared Dev

[https://experimenter-app.dev.mozaws.net/](https://experimenter-app.dev.mozaws.net/)

### Staging

[https://experimenter.stage.mozaws.net/](https://experimenter.stage.mozaws.net/)

### Production

[https://experimenter.services.mozilla.com/](https://experimenter.services.mozilla.com/)


## What is an experiment?

An experiment is a way to measure how a change to your product affects how people use it.

An experiment has three parts:

1. A new feature that can be selectively enabled
1. A group of users to test the new feature
1. Telemetry to measure how people interact with the new feature

## How do I run an experiment?

<p align="center">
  <img src="https://raw.githubusercontent.com/mozilla/experimenter/164/app/experimenter/static/imgs/architecture.png"><br/>
</p>

1. Build a new feature behind a pref flag
1. Define an experiment for that feature in Experimenter
1. Send it to Shield
1. After Shield reviews and approves it, it is sent to Firefox
1. Firefox clients check whether they should enroll in the experiment and configure themselves accordingly
1. Telemetry about the experiment is collected
1. Dashboards are created to visualize the telemetry
1. Analyze and collect the results to understand how the new feature impacted users
1. Do it again!


## Installation

1. Install [docker](https://www.docker.com/) on your machine

1. Clone the repo

        git clone <your fork>

1. Copy the sample env file

        cp .env.sample .env

1. Set DEBUG=True for local development

        vi .env

1. Create a new secret key and put it in .env

        make secretkey

1. Run tests

        make test

1. Run database migrations

        make migrate

1. Make a local user

        make createuser

1. Load the initial data

        make load_locales_countries

1. Run a dev instance

        make up

1. Navigate to it and add an SSL exception to your browser

        https://localhost/

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

### ssl
Create dummy SSL certs to use the dev server over a locally secure
connection. This helps test client behaviour with a secure
connection. This task is run automatically when needed.

### kill
Stop and delete all docker containers.
WARNING: this will remove your database and all data.  Use this to reset your dev environment.

## API

### GET /api/v1/experiments/
List all of the started experiments.

#### Optional Query Parameters
project__slug - Return only the experiments for a given project, an invalid slug will raise 404
status - Return only the experiments with the given status, options are:
- 'Draft'
- 'Review'
- 'Ship'
- 'Accepted'
- 'Live'
- 'Complete'
- 'Rejected'

Example: GET /api/v1/experiments/?project__slug=project-slug&status=Pending

        [
           {
              "accept_url":"https://localhost/api/v1/experiments/self-enabling-needs-based-hardware/accept",
              "client_matching":"Some \"additional\" filtering",
              "locales": [{"code":"en-US", "name": "English (US)"}],
              "countries": [{"code": "US", "name": "United States of America"}],
              "control":{
                 "description":"Eos sunt adipisci beatae. Aut sunt totam maiores reprehenderit sed vero. Nam fugit sequi repellendus cumque. Fugit maxime suscipit eius quas iure exercitationem voluptatibus.",
                 "name":"Seamless 5thgeneration task-force",
                 "ratio":7,
                 "slug":"seamless-5thgeneration-task-force",
                 "value":"\"synergized-client-driven-artificial-intelligence\""
              },
              "end_date":1505767052000.0,
              "experiment_slug":"pref-flip-re-contextualized-systemic-synergy-self-enabling-needs-based-hardware",
              "experiment_url":"https://localhost/experiments/experiment/144/change/",
              "firefox_channel":"Release",
              "firefox_version":"57.0",
              "name":"Self-enabling needs-based hardware",
              "objectives":"Illo maiores libero ratione. Dolorum nostrum molestiae blanditiis cumque. Libero saepe ipsum accusantium maxime.",
              "population_percent":"60.0000",
              "pref_branch":"default",
              "pref_key":"browser.phased.hybrid.implementation.enabled",
              "pref_type":"string",
              "project_name":"Re-contextualized systemic synergy",
              "project_slug":"re-contextualized-systemic-synergy",
              "reject_url":"https://localhost/api/v1/experiments/self-enabling-needs-based-hardware/reject",
              "slug":"self-enabling-needs-based-hardware",
              "start_date":1505767052000.0,
              "variant":{
                 "description":"Modi perferendis repudiandae ducimus dolorem eum rem. Esse porro iure consectetur facere. Quidem nam enim dolore eius ab facilis.",
                 "name":"Business-focused upward-trending Graphic Interface",
                 "ratio":2,
                 "slug":"business-focused-upward-trending-graphic-interface",
                 "value":"\"synchronized-upward-trending-knowledgebase\""
              }
           },
        ]

### GET /api/v1/experiments/<experiment_slug>/
Return a serialization of the requested experiment.

Example: GET /api/v1/experiments/self-enabled-needs-based-hardware/

         {
            "accept_url":"https://localhost/api/v1/experiments/self-enabling-needs-based-hardware/accept",
            "client_matching":"Some \"additional\" filtering",
            "locales": [{"code":"en-US", "name": "English (US)"}],
            "countries": [{"code": "US", "name": "United States of America"}],
            "control":{
               "description":"Eos sunt adipisci beatae. Aut sunt totam maiores reprehenderit sed vero. Nam fugit sequi repellendus cumque. Fugit maxime suscipit eius quas iure exercitationem voluptatibus.",
               "name":"Seamless 5thgeneration task-force",
               "ratio":7,
               "slug":"seamless-5thgeneration-task-force",
               "value":"\"synergized-client-driven-artificial-intelligence\""
            },
            "end_date":1505767052000.0,
            "experiment_slug":"pref-flip-re-contextualized-systemic-synergy-self-enabling-needs-based-hardware",
            "experiment_url":"https://localhost/experiments/experiment/144/change/",
            "firefox_channel":"Release",
            "firefox_version":"57.0",
            "name":"Self-enabling needs-based hardware",
            "objectives":"Illo maiores libero ratione. Dolorum nostrum molestiae blanditiis cumque. Libero saepe ipsum accusantium maxime.",
            "population_percent":"60.0000",
            "pref_branch":"default",
            "pref_key":"browser.phased.hybrid.implementation.enabled",
            "pref_type":"string",
            "addon_name": "Self-Enabling Addon",
            "addon_experiment_id": "self-enabling-addon",
            "addon_testing_url": "https://example.com/testing.xpi",
            "addon_release_url": "https://example.com/release.xpi",
            "project_name":"Re-contextualized systemic synergy",
            "project_slug":"re-contextualized-systemic-synergy",
            "reject_url":"https://localhost/api/v1/experiments/self-enabling-needs-based-hardware/reject",
            "slug":"self-enabling-needs-based-hardware",
            "start_date":1505767052000.0,
            "variant":{
               "description":"Modi perferendis repudiandae ducimus dolorem eum rem. Esse porro iure consectetur facere. Quidem nam enim dolore eius ab facilis.",
               "name":"Business-focused upward-trending Graphic Interface",
               "ratio":2,
               "slug":"business-focused-upward-trending-graphic-interface",
               "value":"\"synchronized-upward-trending-knowledgebase\""
            }
         }


### PATCH /api/v1/experiments/<experiment_slug>/accept
        Body: None

Set the status of a Pending experiment to Accepted.

Example: PATCH /api/v1/experiments/my-first-experiment/accept

### PATCH /api/v1/experiments/<experiment_slug>/reject
        content-type: application/json
        Body: {message: "This experiment was rejected for reasons."}

Set the status of a Pending experiment to Rejected.

Example: PATCH /api/v1/experiments/my-first-experiment/accept

## Contributing

Please see our [Contributing Guidelines](https://github.com/mozilla/experimenter/blob/master/contributing.md)

## License

Experimenter uses the [Mozilla Public License](https://www.mozilla.org/en-US/MPL/)
