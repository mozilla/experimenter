import json

from django import template
from django.utils.safestring import mark_safe

from experimenter.experiments.constants import NimbusConstants
from experimenter.nimbus_ui.constants import (
    APPLICATION_ICON_FILTER_TYPE,
    APPLICATION_ICON_MAP,
    CHANNEL_ICON_FILTER_TYPE,
    CHANNEL_ICON_MAP,
    QA_ICON_FILTER_TYPE,
    QA_STATUS_ICON_MAP,
    STATUS_ICON_FILTER_TYPE,
    STATUS_ICON_MAP,
)

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


@register.filter(name="format_json")
def format_json(value):
    """Formats the JSON value for display by pretty-printing it."""
    try:
        parsed_json = json.dumps(json.loads(value), indent=2)
    except (json.JSONDecodeError, TypeError):
        parsed_json = value

    return mark_safe(
        f'<pre class="text-monospace" style="white-space: pre-wrap; '
        f'word-wrap: break-word;">{parsed_json}</pre>'
    )


@register.filter
def should_show_remote_settings_pending(experiment, reviewer):
    return experiment.should_show_remote_settings_pending(reviewer)


@register.simple_tag(takes_context=True)
def can_review_experiment(context, experiment):
    user = context["request"].user
    return experiment.can_review(user)


@register.filter
def qa_icon_info(value):
    return QA_STATUS_ICON_MAP.get(
        value, QA_STATUS_ICON_MAP[NimbusConstants.QAStatus.NOT_SET]
    )


@register.filter
def application_icon_info(value):
    return APPLICATION_ICON_MAP.get(
        value, APPLICATION_ICON_MAP[NimbusConstants.Application.DESKTOP]
    )


@register.filter
def channel_icon_info(value):
    return NimbusConstants.Channel.get_icon_info(value)


@register.filter
def status_icon_info(value):
    return STATUS_ICON_MAP.get(value, {"icon": "", "color": ""})


@register.simple_tag
def render_channel_icons(experiment):
    channels_data = []

    if experiment.is_desktop and experiment.channels:
        for channel in sorted(experiment.channels):
            icon_info = NimbusConstants.Channel.get_icon_info(channel)
            channel_label = experiment.Channel(channel).label
            channels_data.append(
                {
                    "icon_info": icon_info,
                    "label": channel_label,
                    "is_multi": True,
                }
            )
    elif experiment.channel:
        icon_info = NimbusConstants.Channel.get_icon_info(experiment.channel)
        channel_label = experiment.Channel(experiment.channel).label
        channels_data.append(
            {
                "icon_info": icon_info,
                "label": channel_label,
                "is_multi": False,
            }
        )

    return channels_data


@register.simple_tag
def choices_with_icons(choices, icon_filter_type):
    enriched_choices = []

    for value, label in choices:
        icon_info = None
        if icon_filter_type == QA_ICON_FILTER_TYPE:
            icon_info = QA_STATUS_ICON_MAP.get(
                value, QA_STATUS_ICON_MAP[NimbusConstants.QAStatus.NOT_SET]
            )
        elif icon_filter_type == CHANNEL_ICON_FILTER_TYPE:
            icon_info = CHANNEL_ICON_MAP.get(
                value, CHANNEL_ICON_MAP[NimbusConstants.Channel.NO_CHANNEL]
            )
        elif icon_filter_type == APPLICATION_ICON_FILTER_TYPE:
            icon_info = APPLICATION_ICON_MAP.get(
                value, APPLICATION_ICON_MAP[NimbusConstants.Application.DESKTOP]
            )
        elif icon_filter_type == STATUS_ICON_FILTER_TYPE:
            icon_info = STATUS_ICON_MAP.get(value, {"icon": "", "color": ""})

        enriched_choices.append({"value": value, "label": label, "icon_info": icon_info})

    return enriched_choices


@register.filter
def home_status_display(experiment):
    if not experiment.is_archived and experiment.is_review_timeline:
        return NimbusConstants.PublishStatus.REVIEW

    return experiment.status


@register.filter
def home_status_display_with_icon(experiment):
    status = home_status_display(experiment)
    icon_info = STATUS_ICON_MAP.get(status, {"icon": "", "color": ""})

    return {"status": status, "icon_info": icon_info}
