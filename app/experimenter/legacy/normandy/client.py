import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model


class NormandyError(Exception):
    pass


class NonsuccessfulNormandyCall(NormandyError):
    message = "Normandy API returned Nonsuccessful Response Code"


class APINormandyError(NormandyError):
    message = "Error calling Normandy API"


class NormandyDecodeError(NormandyError):
    message = "Error parsing JSON Normandy Response"


def make_normandy_call(url, params=None):
    if params is None:
        params = {}
    try:
        response = requests.get(url, verify=(not settings.DEBUG), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.exception(f"Normandy API returned Nonsuccessful Response Code: {e}")
        raise NonsuccessfulNormandyCall(*e.args) from e
    except requests.exceptions.RequestException as e:
        logging.exception(f"Error calling Normandy API: {e}")
        raise APINormandyError(*e.args) from e
    except ValueError as e:
        logging.exception(f"Error parsing JSON Normandy response: {e}")
        raise NormandyDecodeError(*e.args) from e


def get_recipe(recipe_id):
    recipe_url = settings.NORMANDY_API_RECIPE_URL.format(id=recipe_id)
    recipe_data = make_normandy_call(recipe_url)
    return recipe_data["approved_revision"]


def get_recipe_list(experiment_slug):
    recipe_url = settings.NORMANDY_API_RECIPES_LIST_URL
    recipe_data = make_normandy_call(
        recipe_url, params={"experimenter_slug": experiment_slug}
    )
    return recipe_data["results"]


def get_recipe_state_enabler(recipe_data):
    # set email default if no email/creator is found in normandy
    enabler_email = settings.NORMANDY_DEFAULT_CHANGELOG_USER

    enabled_states = recipe_data.get("enabled_states", [])
    if len(enabled_states) > 0:
        if creator := enabled_states[0].get("creator"):
            enabler_email = creator.get("email")

    enabler, _ = get_user_model().objects.get_or_create(
        email=enabler_email, username=enabler_email
    )
    return enabler


def get_history_list(recipe_id):
    recipe_url = settings.NORMANDY_API_HISTORY_URL.format(id=recipe_id)
    return make_normandy_call(recipe_url)
