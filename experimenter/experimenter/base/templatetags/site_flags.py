from django import template
from django.utils.html import json_script

from experimenter.base.models import SiteFlag

register = template.Library()


@register.simple_tag(takes_context=True)
def site_flag_extra_data(context, name, element_id):
    """Embed metadata about a given experiment in a page for nimbus-devtools to
    consume.
    """
    if (
        site_flag := SiteFlag.objects.get_cached(context["request"], name)
    ) and site_flag.extra_data is not None:
        return json_script(
            site_flag.extra_data,
            element_id=element_id,
        )

    return ""
