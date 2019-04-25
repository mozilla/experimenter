import json
import requests

from django.conf import settings


class NormandyError(Exception):
    pass


def make_normandy_call(url):
    try:
        return requests.get(url).json()
    except requests.exceptions.RequestException as e:
        logging.exception("Error calling Normandy API: {}".format(e))
        raise NormandyError(*e.args)
    except json.JSONDecodeError as e:
        logging.exception("Error parsing JSON Normandy response: {}".format(e))
        raise NormandyError(*e.args)


def get_recipe_data(recipe_id):
    recipe_url = settings.NORMANDY_API_RECIPE_URL.format(id=recipe_id)
    recipe_data = make_normandy_call(recipe_url)
    return recipe_data['approved_revision']
