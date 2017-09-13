import logging
from decouple import config

from redash_client.client import RedashClient
from redash_client.dashboards.ActivityStreamExperimentDashboard import (
    ActivityStreamExperimentDashboard)

from django.core.management.base import BaseCommand
from experimenter.experiments.models import Experiment


class Command(BaseCommand):
    UT_TEMPLATES_KEY = 'AS Template UT:'
    UT_MAPPED_TEMPLATES_KEY = 'AS Template UT Mapped:'
    help = 'Generates Redash dashboards'

    def generate_dashboards(self):
        api_key = config('REDASH_API_KEY', default='abc123')
        redash_client = RedashClient(api_key)

        relevant_experiments = Experiment.objects.filter(
            status__in=(
                Experiment.STATUS_LAUNCHED,
                Experiment.STATUS_COMPLETE))
        for exp in relevant_experiments:
            try:
                dash = ActivityStreamExperimentDashboard(
                  redash_client,
                  exp.project.name,
                  exp.name,
                  exp.slug,
                  start_date='2017-08-29',
                )
                dash.add_graph_templates(
                    self.UT_MAPPED_TEMPLATES_KEY,
                    dash.MAPPED_UT_EVENTS)
                dash.add_graph_templates(self.UT_TEMPLATES_KEY, dash.UT_EVENTS)

                exp.dashboard_url = dash.public_url
                exp.save()
            except:
                logging.error((
                  'Unable to generate dashboard '
                  'for {experiment}').format(experiment=exp))

    def handle(self, *args, **options):
        self.generate_dashboards()
