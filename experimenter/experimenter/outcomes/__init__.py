import os
import typing
from dataclasses import dataclass

import toml
from django.conf import settings
from django.core.checks import Error, register

from experimenter.experiments.constants import NimbusConstants


@dataclass
class Metric:
    slug: str
    friendly_name: str
    description: str


@dataclass
class Outcome:
    application: str
    description: str
    friendly_name: str
    slug: str
    is_default: bool
    metrics: typing.List[Metric]


class Outcomes:
    _outcomes = None

    @classmethod
    def _load_outcomes(cls):
        outcomes: list[Outcome] = []

        app_name_application_config = {
            a.app_name: a for a in NimbusConstants.APPLICATION_CONFIGS.values()
        }
        for app_name in os.listdir(settings.JETSTREAM_CONFIG_OUTCOMES_PATH):
            app_path = os.path.join(settings.JETSTREAM_CONFIG_OUTCOMES_PATH, app_name)

            for outcome_name in os.listdir(app_path):
                if not outcome_name.endswith(".example"):
                    outcome_path = os.path.join(app_path, outcome_name)

                    with open(outcome_path) as outcome_file:
                        outcome_toml = outcome_file.read()
                        outcome_data = toml.loads(outcome_toml)

                        metrics = []
                        if "metrics" in outcome_data:
                            metrics = [
                                Metric(
                                    slug=metric,
                                    friendly_name=outcome_data["metrics"][metric].get(
                                        "friendly_name"
                                    ),
                                    description=outcome_data["metrics"][metric].get(
                                        "description"
                                    ),
                                )
                                for metric in outcome_data["metrics"]
                            ]

                        outcomes.append(
                            Outcome(
                                application=app_name_application_config[app_name].slug,
                                description=outcome_data["description"],
                                friendly_name=outcome_data["friendly_name"],
                                slug=os.path.splitext(outcome_name)[0],
                                is_default=False,
                                metrics=metrics,
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
