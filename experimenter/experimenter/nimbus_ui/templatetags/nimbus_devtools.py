from django import template
from django.utils.html import json_script

from experimenter.experiments.models import NimbusExperiment

register = template.Library()


@register.simple_tag
def devtools_metadata(experiment: NimbusExperiment) -> str:
    """Embed metadata about a given experiment in a page for nimbus-devtools to
    consume.
    """
    return json_script(
        {
            "application": experiment.application,
            "isLocalized": experiment.is_localized,
            "localizations": experiment.localizations,
        },
        element_id="nimbus-devtools-experiment-metadata",
    )


@register.simple_tag
def devtools_integration(experiment: NimbusExperiment, page: str) -> str:
    """Embed metadata about a given experiment and the current page for
    nimbus-devtools to consume.
    """
    return json_script(
        {
            "experimentMetadata": {
                "application": experiment.application,
                "isLocalized": experiment.is_localized,
                "localizations": experiment.localizations,
            },
            "page": page,
        },
        element_id="nimbus-devtools-integration",
    )
