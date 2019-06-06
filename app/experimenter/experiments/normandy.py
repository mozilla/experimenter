import requests
import logging
from django.conf import settings


class NormandyError(Exception):
    pass


class NonsuccessfulNormandyCall(NormandyError):
    message = "Normandy API returned Nonsuccessful Response Code"


class APINormandyError(NormandyError):
    message = "Error calling Normandy API"


class NormandyDecodeError(NormandyError):
    message = "Error parsing JSON Normandy Response"


def make_normandy_call(url):
    try:
        response = requests.get(url)
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


def get_recipe(recipe_id):
    recipe_url = settings.NORMANDY_API_RECIPE_URL.format(id=recipe_id)
    recipe_data = make_normandy_call(recipe_url)
    return recipe_data["approved_revision"]
