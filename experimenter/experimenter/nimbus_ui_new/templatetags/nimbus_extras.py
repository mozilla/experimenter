from django import template
from django.utils.safestring import mark_safe

from experimenter.experiments.constants import NimbusConstants

register = template.Library()


@register.simple_tag(takes_context=True)
def pagination_url(context, page, **kwargs):
    """Template tag to attach the page number to any existing querystrings.

    Usage:

        <a href="{% pagination_url 3 %}">Go to page 3</a>

    Will, yield this output:

        <a href="?page=3">Go to page 3</a>

    If the current URL already was `...?foo=bar` the output would be

        <a href="?foo=bar&amp;page=3">Go to page 3</a>

    You can also use complex object instead of hardcoded numbers.
    E.g.:

        <a href="{% pagination_url page_obj.previous_page_number %}">Prev</a>

    Note that, if the next page is going to 1 it *removes* the page key
    entirely. That's so that if you're on page 2 and want to link back
    to the homepage, at page 1, you'll end up with a "clean" link like
    this:

        <a href="">Page 1</a>

    """
    data = context["request"].GET.copy()
    if page == 1:
        data.pop("page", None)
    else:
        data["page"] = page
    if data:
        return f"?{data.urlencode()}"
    else:
        return "."


@register.filter
def parse_version(version_str):
    if version_str:
        return NimbusConstants.Version.parse(version_str)
    return "No Version"


@register.filter(name="remove_underscores")
def remove_underscores(value):
    """Replace underscores in the string with spaces."""
    return value.replace("_", " ")


@register.filter(name="format_not_set")
def format_not_set(value):
    """Formats the given value to display 'Not set' in red if it's empty or None."""
    if value in [None, "", "NOT SET"]:
        return mark_safe('<span class="text-danger">Not set</span>')
    return value
