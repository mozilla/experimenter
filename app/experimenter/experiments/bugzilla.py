import json
import logging
import requests

from django.conf import settings


def format_bug_body(experiment):
    bug_body = ""

    if experiment.is_addon_study:
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
    elif experiment.is_pref_study:
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
    response_data = {}
    try:
        response = requests.post(url, data)
        response_data = json.loads(response.content)

        if response.status_code >= 400:
            logging.info(
                "Error creating Bugzilla Ticket: {error}".format(
                    error=response_data.get("message")
                )
            )
    except requests.exceptions.RequestException:
        logging.exception("Error calling Bugzilla API")
    except json.JSONDecodeError:
        logging.exception("Error parsing JSON Bugzilla response")

    return response_data.get("id", None)


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
    }

    return make_bugzilla_call(settings.BUGZILLA_CREATE_URL, bug_data)


def add_experiment_comment(experiment):
    comment_data = {"comment": format_bug_body(experiment)}

    return make_bugzilla_call(
        settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
        comment_data,
    )
