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


def create_experiment_bug(experiment):
    bug_data = {
        "product": "Shield",
        "component": "Shield Study",
        "version": "unspecified",
        "summary": "[Shield] {experiment}".format(experiment=experiment),
        "description": format_bug_body(experiment),
        "assigned_to": experiment.owner.email,
        "cc": settings.BUGZILLA_CC_LIST,
    }

    response_data = {}
    try:
        response = requests.post(settings.BUGZILLA_CREATE_URL, bug_data)
        response_data = json.loads(response.content)
    except requests.exceptions.RequestException:
        logging.exception("Error creating Bugzilla Ticket")
    except json.JSONDecodeError:
        logging.exception("Error parsing JSON Bugzilla response")

    return response_data.get("id", None)
