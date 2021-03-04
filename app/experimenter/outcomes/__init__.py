import os
from dataclasses import dataclass

import toml
from django.conf import settings
from django.core.checks import Error, register

from experimenter.experiments.constants import NimbusConstants


@dataclass
class Outcome:
    application: str
    app_name: str
    description: str
    friendly_name: str
    slug: str


class Outcomes:
    _outcomes = None

    @classmethod
    def _load_outcomes(cls):
        outcomes = []

        for app_name in os.listdir(settings.JETSTREAM_CONFIG_OUTCOMES_PATH):
            app_path = os.path.join(settings.JETSTREAM_CONFIG_OUTCOMES_PATH, app_name)

            for outcome_name in os.listdir(app_path):
                if not outcome_name.endswith(".example"):
                    outcome_path = os.path.join(app_path, outcome_name)

                    with open(outcome_path, "r") as outcome_file:
                        outcome_toml = outcome_file.read()
                        outcome_data = toml.loads(outcome_toml)

                        outcomes.append(
                            Outcome(
                                application=NimbusConstants.APP_NAME_APPLICATION[
                                    app_name
                                ],
                                app_name=app_name,
                                description=outcome_data["description"],
                                friendly_name=outcome_data["friendly_name"],
                                slug=os.path.splitext(outcome_name)[0],
                            )
                        )

        return outcomes

    @classmethod
    def clear_cache(cls):
        cls._outcomes = None

    @classmethod
    def all(cls):
        if cls._outcomes is None:
            cls._outcomes = cls._load_outcomes()

        return cls._outcomes

    @classmethod
    def by_application(cls, application):
        return [o for o in cls.all() if o.application == application]


@register()
def check_outcome_tomls(app_configs, **kwargs):
    errors = []

    try:
        Outcomes.all()
    except Exception as e:
        errors.append(Error(f"Error loading Outcome TOMLS {e}"))
    return errors
