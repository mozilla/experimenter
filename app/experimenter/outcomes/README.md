# Outcomes

## Overview

[Outcomes](https://github.com/mozilla/jetstream-config/#outcome-snippets) define automated analyses that can be applied to Nimbus experiments. They are stored in the [Jetstream Config repo](https://github.com/mozilla/jetstream-config/tree/main/outcomes) as [TOML](https://github.com/toml-lang/toml) files and are consumed by Experimenter as a [Git Submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules).

## Building and Deploying

Every time the Experimenter Docker container is built, it will synchronize the Jetstream Config repo into the local Experimenter source tree, which will then be copied with the rest of Experimenter's source into the Docker container. The Outcomes module will load the outcome definition TOMLs into memory where they can be accessed.

## Using Outcomes

Outcomes can be accessed by using the Outcome and Outcomes classes. An Outcome has the following properties:

- `application: str` An application ID defined as one of `("fenix", "firefox-desktop")`
- `app_name: str` An application name defined as one of `("fenix", "firefox_desktop")`
- `description: str` A helpful description to display in Experimenter's UI when choosing outcomes
- `friendly_name: str` A name to display in Experimenter's UI when choosing outcomes
- `slug: str` A unique identifier to include in the experiment DTO when deploying experiments

```py
from experimenter.experiments.constants import NimbusConstants
from experimenter.outcomes import Outcomes

# All outcomes for all applications
for outcome in Outcomes.all():
    print(outcome.slug)

# All outcomes for a given application
for outcome in Outcomes.by_app_id(NimbusConstants.Application.FENIX):
    print(outcome.slug)
```

## Consistency

A Nimbus experiment stores the slugs of the outcomes that are selected by an experiment's owner when it is created. After that point, the set of outcomes stored in the Jetstream Config repo may change in any way at any time, and so by the time the experiment is complete and analyzed by Jetstream, the set of outcome slugs stored on the experiment and the set of outcome slugs stored in the Jetstream Config repo may differ, in which case Jetstream will find the set of slugs that match and analyze those, disregarding any that were selected by the experiment owner that no longer match any definition in Jetstream Config.
