import logging
import requests
from urllib.parse import urlparse, parse_qs

from django.conf import settings

INVALID_USER_ERROR_CODE = 51
INVALID_PARAMETER_ERROR_CODE = 53


class BugzillaError(Exception):
    pass


def format_bug_body(experiment):
    bug_body = ""
    countries = "all"
    locales = "all"
    if experiment.countries.count() > 0:
        countries = "".join(
            [
                "{name} ({code}) ".format(name=country.name, code=country.code)
                for country in list(experiment.countries.all())
            ]
        )
    if len(experiment.locales.all()) > 0:
        locales = "".join(
            [
                "{name} ({code}) ".format(name=locale.name, code=locale.code)
                for locale in list(experiment.locales.all())
            ]
        )

    if experiment.is_addon_experiment:
        variants_body = "\n".join(
            [
                experiment.BUGZILLA_VARIANT_ADDON_TEMPLATE.format(
                    variant=variant
                )
                for variant in experiment.variants.all()
            ]
        )
        bug_body = experiment.BUGZILLA_ADDON_TEMPLATE.format(
            experiment=experiment,
            variants=variants_body,
            countries=countries,
            locales=locales,
        )
    elif experiment.is_pref_experiment:
        variants_body = "\n".join(
            [
                experiment.BUGZILLA_VARIANT_PREF_TEMPLATE.format(
                    variant=variant
                )
                for variant in experiment.variants.all()
            ]
        )
        bug_body = experiment.BUGZILLA_PREF_TEMPLATE.format(
            experiment=experiment,
            variants=variants_body,
            countries=countries,
            locales=locales,
        )

    return bug_body


def format_update_body(experiment):
    summary = "[Experiment] {experiment_name} Fx {version} {channel}".format(
        experiment_name=experiment,
        version=experiment.format_firefox_versions,
        channel=experiment.firefox_channel,
    )
    return {"summary": summary, "cf_user_story": format_bug_body(experiment)}


def update_experiment_bug(experiment):
    body = format_update_body(experiment)
    make_bugzilla_call(
        settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
        requests.put,
        data=body,
    )


def user_exists(user):
    try:
        response = make_bugzilla_call(
            settings.BUGZILLA_USER_URL.format(email=user), requests.get
        )
        users = response["users"]
        return len(users) == 1
    except (BugzillaError, KeyError):
        return False


def format_resolution_body(experiment):
    if experiment.status == experiment.STATUS_COMPLETE:
        return {"status": "RESOLVED", "resolution": "FIXED"}
    elif experiment.archived:
        return {"status": "RESOLVED", "resolution": "WONTFIX"}
    else:
        return {"status": "REOPENED"}


def bug_exists(bug_id):
    try:
        response = make_bugzilla_call(
            settings.BUGZILLA_BUG_URL.format(bug_id=bug_id), requests.get
        )
        bugs = response["bugs"]
        return len(bugs) == 1
    except (BugzillaError, KeyError):
        return False


def update_bug_resolution(experiment):
    if experiment.bugzilla_id:
        logging.info("Bugzilla Resolution/Status")
        status_body = format_resolution_body(experiment)
        make_bugzilla_call(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            requests.put,
            status_body,
        )


def make_bugzilla_call(url, method, data=None):
    try:
        response = method(url, data)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling Bugzilla API: {}".format(e))
        raise BugzillaError(*e.args)
    except ValueError as e:
        logging.exception("Error parsing JSON Bugzilla response: {}".format(e))
        raise BugzillaError(*e.args)


def format_creation_bug_body(experiment, extra_fields):
    bug_data = {
        "product": "Shield",
        "component": "Shield Study",
        "version": "unspecified",
        "summary": "[Experiment]: {experiment}".format(experiment=experiment),
        "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
            experiment=experiment
        ),
        "cc": settings.BUGZILLA_CC_LIST,
        "type": "task",
        "priority": "P3",
        "url": experiment.experiment_url,
    }
    bug_data.update(extra_fields)
    return bug_data


def create_experiment_bug(experiment):
    assigned_to, see_also, blocks = None, None, None

    if user_exists(experiment.owner.email):
        assigned_to = experiment.owner.email

    see_also = set_bugzilla_id_value(experiment.data_science_bugzilla_url)
    blocks = set_bugzilla_id_value(experiment.feature_bugzilla_url)

    extra_fields = {
        "assigned_to": assigned_to,
        "see_also": see_also,
        "blocks": blocks,
    }

    bug_data = format_creation_bug_body(experiment, extra_fields)
    response_data = make_bugzilla_call(
        settings.BUGZILLA_CREATE_URL, requests.post, data=bug_data
    )

    if "id" not in response_data:
        raise BugzillaError(response_data["message"])
    return response_data["id"]


def get_bugzilla_id(bug_url):
    query = urlparse(bug_url).query
    bugzilla_id = parse_qs(query).get("id", [""])[0]
    if bugzilla_id.isnumeric():
        return int(bugzilla_id)


def set_bugzilla_id_value(bug_url):
    data_science_bug_id = get_bugzilla_id(bug_url)
    if data_science_bug_id and bug_exists(data_science_bug_id):
        return [data_science_bug_id]


def add_experiment_comment(experiment, comment):
    comment_data = {"comment": comment}
    response_data = make_bugzilla_call(
        settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
        requests.post,
        comment_data,
    )

    return response_data["id"]
