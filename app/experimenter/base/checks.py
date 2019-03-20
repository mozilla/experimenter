import re

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.checks import Error, Warning, register as register_check


ERROR_BUGZILLA_SETTINGS = "experimenter.base.E001"
WARNING_BUGZILLA_SETTINGS = "experimenter.base.W001"


def check_bugzilla_settings(app_configs, **kwargs):
    problems = []
    url_settings = (
        "BUGZILLA_CREATE_URL",
        "BUGZILLA_DETAIL_URL",
        "BUGZILLA_COMMENT_URL",
    )
    url_validator = validators.URLValidator()
    for setting in url_settings:
        url = getattr(settings, setting)
        try:
            url_validator(url)
        except ValidationError:
            scrubbed = re.sub(r"api_key=(\w+)", "api_key=...", url)
            problems.append(
                Error(
                    f"settings.{setting} ({scrubbed!r}) "
                    f"is not a valid Buzilla URL",
                    hint=f"Edit your .env file for {setting!r}",
                    id=ERROR_BUGZILLA_SETTINGS,
                )
            )
    if not settings.BUGZILLA_API_KEY:
        problems.append(
            Warning(
                f"settings.BUGZILLA_API_KEY is not set.",
                id=WARNING_BUGZILLA_SETTINGS,
            )
        )
    return problems


def register():
    register_check(check_bugzilla_settings)
