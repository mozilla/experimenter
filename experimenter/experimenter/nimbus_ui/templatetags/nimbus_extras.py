import json
from datetime import date

import humanize
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


@register.filter
def to_str(value):
    return str(value)


@register.filter
def experiment_date_progress(experiment):
    today = date.today()

    result = {
        "show_bar": False,
        "bar_class": "",
        "bar_style": "",
        "days_text": "",
        "progress_percentage": 0,
        "is_overdue": False,
        "is_complete": False,
        "is_na": True,
        "has_alert": False,
        "start_date": None,
        "end_date": None,
        "date_range_text": "",
    }

    # Early states (Draft, Preview, Review) - show N/A
    if experiment.is_draft or experiment.is_preview or experiment.is_review_timeline:
        result["days_text"] = "N/A"
        return result

    start_date = experiment.enrollment_start_date
    end_date = experiment.computed_end_date

    if start_date:
        result["start_date"] = start_date.strftime("%b %d, %Y")
    if end_date:
        result["end_date"] = end_date.strftime("%b %d, %Y")

    if start_date and end_date:
        result["date_range_text"] = (
            f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        )

    total_days = experiment.computed_duration_days
    if not total_days or total_days <= 0:
        total_days = (end_date - start_date).days if end_date and start_date else 1

    if experiment.is_complete:
        result.update(
            {
                "show_bar": True,
                "bar_class": "bg-secondary",
                "bar_style": "width: 100%",
                "days_text": "Complete",
                "progress_percentage": 100,
                "is_complete": True,
                "is_na": False,
            }
        )
    elif experiment.is_started and start_date and end_date:
        days_since_start = (today - start_date).days
        days_remaining = (end_date - today).days

        # Calculate total days
        total_days = experiment.computed_duration_days
        if not total_days or total_days <= 0:
            total_days = (end_date - start_date).days if end_date and start_date else 1

        if days_remaining < 0:
            # Overdue
            result.update(
                {
                    "show_bar": True,
                    "bar_class": "bg-danger",
                    "bar_style": "width: 100%",
                    "days_text": f"{days_remaining} days",
                    "progress_percentage": 100,
                    "is_overdue": True,
                    "is_na": False,
                    "has_alert": True,
                }
            )
        else:
            progress_percentage = min(
                100, max(0, (days_since_start / max(1, total_days)) * 100)
            )

            bar_class = "bg-success" if experiment.is_enrolling else "bg-info"

            result.update(
                {
                    "show_bar": True,
                    "bar_class": bar_class,
                    "bar_style": f"width: {progress_percentage}%",
                    "days_text": f"{days_remaining} days",
                    "progress_percentage": progress_percentage,
                    "is_na": False,
                }
            )
    else:
        # default show N/A
        result["days_text"] = "N/A"

    return result


@register.filter
def short_number(value, precision=1):
    formatted_number = str(value)
    formatted_number_components = humanize.intword(value, format=f"%.{precision}f").split(
        " "
    )
    number = formatted_number_components[0]

    if len(formatted_number_components) > 1:
        magnitude = formatted_number_components[1]
        if magnitude == "thousand":
            magnitude = "K"
        formatted_number = f"{number}{magnitude[0].capitalize()}"

    return formatted_number


@register.filter
def format_string(value, arg):
    """Format a string with a single placeholder {text}.

    Usage:
        {{ "Subscribe to {text}"|format_string:feature.name }}
    """
    return value.format(text=arg)


@register.filter
def to_percentage(value, precision=None):
    percentage_value = value * 100

    if precision is None:
        return f"{percentage_value}%"

    format_string = f"{{:.{precision}f}}%"
    return format_string.format(percentage_value)
