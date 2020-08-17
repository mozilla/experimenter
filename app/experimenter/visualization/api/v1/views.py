import json
import logging
import requests

from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.core.files.storage import default_storage


class VisualizationView(View):
    EXPERIMENTER_API_URL = "https://experimenter.services.mozilla.com/api/v1/experiments"

    def get_experiment_data(self, experiment_url):
        try:
            response = requests.get(experiment_url, verify=(not settings.DEBUG))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.exception(
                "Experimenter API returned Nonsuccessful Response Code: {}".format(e)
            )
        except requests.exceptions.RequestException as e:
            logging.exception("Error calling Experimenter API: {}".format(e))
        except ValueError as e:
            logging.exception("Error parsing JSON Experimenter response: {}".format(e))

        return {}

    def get(self, request, *args, **kwargs):
        # TODO: Normandy slug should come from the experiment object rather than the API.

        slug = self.kwargs['slug']
        experiment_url = f'''{self.EXPERIMENTER_API_URL}/{slug}''';
        experiment_data = self.get_experiment_data(experiment_url)
        normandy_slug = experiment_data.get("normandy_slug", None).replace("-", "_")

        daily_data_filename = f'''statistics_{normandy_slug}_daily.json'''
        weekly_data_filename = f'''statistics_{normandy_slug}_weekly.json'''

        experiment_json = {
            "daily": json.loads(
                default_storage.open(daily_data_filename).read().decode('utf8')
            ),
            "weekly": json.loads(
                default_storage.open(weekly_data_filename).read().decode('utf8')
            )
        }

        return HttpResponse(json.dumps(experiment_json))
