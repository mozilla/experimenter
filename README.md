# ![Logo](https://raw.githubusercontent.com/mozilla/experimenter/master/app/experimenter/static/imgs/favicon_24.png) Experimenter 
[![CircleCI](https://circleci.com/gh/mozilla/experimenter.svg?style=svg)](https://circleci.com/gh/mozilla/experimenter)

<p align="center">
  <img src="https://cdn1.iconfinder.com/data/icons/simple-arrow/512/arrow_20-128.png"><br/>
  <b>1. Design 2. Launch 3. Analyze</b>
  <br><br>
</p>

Experimenter is a platform for managing experiments in [Mozilla Firefox](https://www.mozilla.org/en-US/firefox/?utm_medium=referral&utm_source=firefox-com). 

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

1. Create a new secret key and put it in .env

        make secretkey

1. Run tests

        make test

1. Run database migrations

        make migrate

1. Make a local user

        make createuser

1. Run a dev instance

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
status - Return only the experiments with the given status, options are:
- 'Created'
- 'Pending'
- 'Accepted'
- 'Launched'
- 'Complete'
- 'Rejected'

Example: GET /api/v1/experiments/?project__slug=project-slug&status=Pending

        [
           {
              "project_name":"Monitored empowering website",
              "name":"Devolved real-time groupware",
              "slug":"devolved-real-time-groupware",
              "experiment_slug":"pref-flip-monitored-empowering-website-devolved-real-time-groupware",
              "experiment_url":"https://localhost/experiments/experiment/143/change/",
              "accept_url":"https://localhost/api/v1/experiments/devolved-real-time-groupware/accept",
              "reject_url":"https://localhost/api/v1/experiments/devolved-real-time-groupware/reject",
              "firefox_version":"57.0",
              "firefox_channel":"Nightly",
              "population_percent":"100.0000",
              "objectives":"Placeat ducimus impedit inventore ipsam laboriosam fugit architecto. Animi accusamus at excepturi nisi expedita placeat eaque. Maxime sint nisi dicta illum.",
              "pref_key":"browser.ergonomic.6thgeneration.focus.group.enabled",
              "pref_type":"boolean",
              "variant":{
                 "name":"Intuitive disintermediate standardization",
                 "slug":"intuitive-disintermediate-standardization",
                 "description":"A in quaerat adipisci dignissimos nam esse maiores. Tempora fugit corporis possimus fuga sit praesentium nemo. Molestias ducimus eius qui nihil recusandae minima.",
                 "ratio":7,
                 "value":false
              },
              "control":{
                 "name":"Profit-focused zero administration throughput",
                 "slug":"profit-focused-zero-administration-throughput",
                 "description":"Aliquid id placeat iure alias. Cum facere vel voluptatibus corporis dolore. Sint cupiditate aut earum tempora quas.",
                 "ratio":8,
                 "value":true
              }
           }
        ]


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

1. Fork the repo!
1. File a new issue describing the change you want to make: Change the things #123
1. Create your feature branch with the issue number: `git checkout -b 123`
1. Commit your changes: `git commit -am 'Changed the things fixes #123'`
1. Push to the branch: `git push origin 123`
1. Submit a pull request :D


## License

Experimenter uses the [Mozilla Public License](https://www.mozilla.org/en-US/MPL/)
