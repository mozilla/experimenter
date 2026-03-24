from django import template
from django.utils.html import json_script

register = template.Library()


@register.simple_tag
def devtools_metadata(experiment):
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
