from typing import Callable, List, Mapping, Optional, TypedDict, Union, Literal
from urllib.parse import urlparse, parse_qs
import logging
import requests

from django.conf import settings
from experimenter.experiments.models import Experiment

INVALID_USER_ERROR_CODE = 51
INVALID_PARAMETER_ERROR_CODE = 53
EXPERIMENT_NAME_MAX_LEN = 150


class BugzillaError(Exception):
    pass


class BugzillaAPIData(TypedDict, total=False):
    assigned_to: Optional[str]
    blocks: Optional[List[int]]
    bugs: List[int]
    cc: str
    cf_user_story: str
    comment: str
    component: str
    description: str
    id: str
    message: str
    priority: str
    product: str
    resolution: Union[Literal["FIXED"], Literal["WONTFIX"]]
    status: Union[Literal["REOPENED"], Literal["RESOLVED"]]
    summary: str
    type: str
    url: str
    users: List[str]
    version: str


def get_bugzilla_id(bug_url: str) -> Optional[int]:
    query = urlparse(bug_url).query
    bugzilla_id = parse_qs(query).get("id", [""])[0]
    if bugzilla_id.isnumeric():
        return int(bugzilla_id)
    return None


def make_bugzilla_call(
    url: str,
    method: Callable[[str, Optional[Mapping]], requests.Response],
    data: Optional[BugzillaAPIData] = None,
) -> BugzillaAPIData:
    try:
        return method(url, data).json()
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling Bugzilla API: {}".format(e))
        raise BugzillaError(*e.args)
    except ValueError as e:
        logging.exception("Error parsing JSON Bugzilla response: {}".format(e))
        raise BugzillaError(*e.args)


def user_exists(user: str) -> bool:
    try:
        response = make_bugzilla_call(
            settings.BUGZILLA_USER_URL.format(email=user), requests.get
        )
        users = response["users"]
        return len(users) == 1
    except (BugzillaError, KeyError):
        return False


def bug_exists(bug_id: int) -> bool:
    try:
        response = make_bugzilla_call(
            settings.BUGZILLA_BUG_URL.format(bug_id=bug_id), requests.get
        )
        bugs = response["bugs"]
        return len(bugs) == 1
    except (BugzillaError, KeyError):
        return False


def add_experiment_comment(bugzilla_id: str, comment: str) -> str:
    return make_bugzilla_call(
        settings.BUGZILLA_COMMENT_URL.format(id=bugzilla_id),
        requests.post,
        {"comment": comment},
    )["id"]


def format_bug_body(experiment: Experiment) -> str:
    bug_body = ""
    countries = "all"
    locales = "all"
    if experiment.countries.count():
        countries = "".join(
            [
                "{name} ({code}) ".format(name=country.name, code=country.code)
                for country in list(experiment.countries.all())
            ]
        )
    if experiment.locales.count():
        locales = "".join(
            [
                "{name} ({code}) ".format(name=locale.name, code=locale.code)
                for locale in list(experiment.locales.all())
            ]
        )

    if experiment.is_addon_experiment:
        variants_body = "\n".join(
            [
                experiment.BUGZILLA_VARIANT_ADDON_TEMPLATE.format(variant=variant)
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
                experiment.BUGZILLA_VARIANT_PREF_TEMPLATE.format(variant=variant)
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


def format_update_body(experiment: Experiment) -> BugzillaAPIData:
    summary = "[Experiment] {experiment_name} Fx {version} {channel}".format(
        experiment_name=experiment,
        version=experiment.format_firefox_versions,
        channel=experiment.firefox_channel,
    )
    return {"summary": summary, "cf_user_story": format_bug_body(experiment)}


def format_resolution_body(experiment: Experiment) -> BugzillaAPIData:
    if experiment.status == experiment.STATUS_COMPLETE:
        return {"status": "RESOLVED", "resolution": "FIXED"}
    elif experiment.archived:
        return {"status": "RESOLVED", "resolution": "WONTFIX"}
    else:
        return {"status": "REOPENED"}


def format_creation_bug_body(
    experiment: Experiment, extra_fields: BugzillaAPIData
) -> BugzillaAPIData:
    summary = format_summary(experiment)
    bug_data: BugzillaAPIData = {
        "product": "Shield",
        "component": "Shield Study",
        "version": "unspecified",
        "summary": summary,
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


def format_summary(experiment: Experiment) -> str:
    truncated_name = experiment.name[0:EXPERIMENT_NAME_MAX_LEN]

    if truncated_name != experiment.name:
        truncated_name += "..."

    return "[Experiment]: {type}: {experiment}".format(
        type=experiment.get_type_display(), experiment=truncated_name
    )


def format_normandy_experiment_request(experiment: Experiment) -> BugzillaAPIData:
    assigned_to, blocks = None, None

    if experiment.owner and user_exists(experiment.owner.email):
        assigned_to = experiment.owner.email

    if experiment.feature_bugzilla_url:
        feature_bug_id = get_bugzilla_id(experiment.feature_bugzilla_url)
        if feature_bug_id and bug_exists(feature_bug_id):
            blocks = [feature_bug_id]

    return format_creation_bug_body(
        experiment, {"assigned_to": assigned_to, "blocks": blocks}
    )


def format_rapid_experiment_request(experiment: Experiment) -> BugzillaAPIData:
    summary = format_summary(experiment)
    bug_data: BugzillaAPIData = {
        "product": "Shield",
        "component": "Shield Study",
        "version": "unspecified",
        "type": "task",
        "summary": summary,
        "description": experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE,
    }

    if experiment.owner and user_exists(experiment.owner.email):
        bug_data["assigned_to"] = experiment.owner.email

    return bug_data


def create_experiment_bug(experiment: Experiment) -> str:
    if experiment.is_rapid_experiment:
        bug_data = format_rapid_experiment_request(experiment)
    else:
        bug_data = format_normandy_experiment_request(experiment)

    response_data = make_bugzilla_call(
        settings.BUGZILLA_CREATE_URL, requests.post, data=bug_data
    )

    if "id" not in response_data:
        raise BugzillaError(response_data["message"])
    return response_data["id"]


def update_experiment_bug(experiment: Experiment) -> None:
    body = format_update_body(experiment)
    make_bugzilla_call(
        settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
        requests.put,
        data=body,
    )


def update_bug_resolution(experiment: Experiment) -> None:
    if experiment.bugzilla_id:
        status_body = format_resolution_body(experiment)
        make_bugzilla_call(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            requests.put,
            status_body,
        )
