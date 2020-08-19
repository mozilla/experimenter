import json
import logging
import requests

from experimenter.experiments.models import Experiment

from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.core.files.storage import default_storage


class VisualizationView(View):

    def load_data_from_gcs(self, filename):
        return json.loads(
            default_storage.open(filename).read().decode('utf8')
        ) if default_storage.exists(filename) else []

    def get(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        current_expermient_arr = Experiment.objects.get_prefetched().filter(slug=slug)
        if (len(current_expermient_arr) < 1):
            return HttpResponse('')

        recipe_slug = current_expermient_arr[0].recipe_slug.replace("-", "_")

        daily_data_filename = f'''statistics_{recipe_slug}_daily.json'''
        weekly_data_filename = f'''statistics_{recipe_slug}_weekly.json'''

        daily_data = self.load_data_from_gcs(daily_data_filename)
        weekly_data = self.load_data_from_gcs(weekly_data_filename)

        experiment_json = {
            "daily": daily_data,
            "weekly": weekly_data
        };

        return HttpResponse(json.dumps(experiment_json))
