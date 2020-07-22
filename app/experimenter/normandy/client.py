from typing import List, Mapping, TypedDict, Optional

import requests
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User


class NormandyError(Exception):
    pass


class NonsuccessfulNormandyCall(NormandyError):
    message = "Normandy API returned Nonsuccessful Response Code"


class APINormandyError(NormandyError):
    message = "Error calling Normandy API"


class NormandyDecodeError(NormandyError):
    message = "Error parsing JSON Normandy Response"


class Creator(TypedDict, total=False):
    email: str


class EnabledStates(TypedDict, total=False):
    creator: Creator


class RecipeArguments(TypedDict, total=False):
    isEnrollmentPaused: bool


class RecipeRevision(TypedDict, total=False):
    arguments: RecipeArguments
    creator: Creator
    enabled_states: List[EnabledStates]
    enabled: bool
    filter_object: Mapping


class Recipe(TypedDict, total=False):
    approved_revision: RecipeRevision
    id: int
    latest_revision: RecipeRevision


class Results(TypedDict, total=False):
    results: List[Recipe]


def make_normandy_call(url: str, params: Optional[Mapping[str, str]] = None) -> Mapping:
    try:
        response = requests.get(url, verify=(not settings.DEBUG), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.exception(
            "Normandy API returned Nonsuccessful Response Code: {}".format(e)
        )
        raise NonsuccessfulNormandyCall(*e.args)
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling Normandy API: {}".format(e))
        raise APINormandyError(*e.args)
    except ValueError as e:
        logging.exception("Error parsing JSON Normandy response: {}".format(e))
        raise NormandyDecodeError(*e.args)


def get_recipe(recipe_id: Optional[int]) -> RecipeRevision:
    return make_normandy_call(settings.NORMANDY_API_RECIPE_URL.format(id=recipe_id))[
        "approved_revision"
    ]


def get_recipe_list(experiment_slug: str,) -> List[Recipe]:
    return make_normandy_call(
        settings.NORMANDY_API_RECIPES_LIST_URL,
        params={"experimenter_slug": experiment_slug},
    )["results"]


def get_recipe_state_enabler(recipe_data: RecipeRevision) -> User:
    # set email default if no email/creator is found in normandy
    enabler_email = settings.NORMANDY_DEFAULT_CHANGELOG_USER

    enabled_states = recipe_data.get("enabled_states", [])
    if len(enabled_states) > 0:
        creator = enabled_states[0].get("creator")
        if creator and "email" in creator:
            enabler_email = creator["email"]

    enabler, _ = get_user_model().objects.get_or_create(
        email=enabler_email, username=enabler_email
    )
    return enabler
