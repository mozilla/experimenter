import json
import logging
import requests

from django.conf import settings


INVALID_USER_ERROR_CODE = 51


class BugzillaError(Exception):
    pass


def format_bug_body(experiment):
    bug_body = ""

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
            experiment=experiment, variants=variants_body
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
            experiment=experiment, variants=variants_body
        )

    return bug_body


def make_bugzilla_call(url, data):
    try:
        response = requests.post(url, data)
        return json.loads(response.content)
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling Bugzilla API: {}".format(e))
        raise BugzillaError(*e.args)
    except json.JSONDecodeError as e:
        logging.exception("Error parsing JSON Bugzilla response: {}".format(e))
        raise BugzillaError(*e.args)


def create_experiment_bug(experiment):
    bug_data = {
        "product": "Shield",
        "component": "Shield Study",
        "version": "unspecified",
        "summary": "[Shield] {experiment}".format(experiment=experiment),
        "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
            experiment=experiment
        ),
        "assigned_to": experiment.owner.email,
        "cc": settings.BUGZILLA_CC_LIST,
        "type": "task",
        "priority": "P3",
    }

    response_data = make_bugzilla_call(settings.BUGZILLA_CREATE_URL, bug_data)

    # The experiment owner might not exist in bugzilla
    # in which case we try to create it again with no assignee
    if response_data.get("code", None) == INVALID_USER_ERROR_CODE:
        bug_data = bug_data.copy()
        del bug_data["assigned_to"]
        response_data = make_bugzilla_call(
            settings.BUGZILLA_CREATE_URL, bug_data
        )
    try:
        return response_data["id"]
    except KeyError:
        raise BugzillaError


def add_experiment_comment(experiment):
    comment_data = {"comment": format_bug_body(experiment)}

    response_data = make_bugzilla_call(
        settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
        comment_data,
    )

    return response_data["id"]
