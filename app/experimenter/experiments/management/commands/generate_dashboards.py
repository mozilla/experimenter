import logging
from datetime import datetime, timezone, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from stmoab.StatisticalDashboard import StatisticalDashboard

from experimenter.experiments.models import Experiment, ExperimentChangeLog


class Command(BaseCommand):
    POPULATION_TEMPLATE = 'UT Experiment Template: Population Size'
    EVENTS_PER_HOUR_TEMPLATE = 'TTests Template Per Hour UT Five:'
    UT_HOURLY_TTABLE = 'Statistical Analysis (Per Active Hour) - UT'
    help = 'Generates Redash dashboards'

    def generate_dashboards(self):
        recent_changelog_complete = ExperimentChangeLog.objects.filter(
            old_status=Experiment.STATUS_LAUNCHED,
            new_status=Experiment.STATUS_COMPLETE).filter(
            changed_on__gte=(datetime.now(timezone.utc) - timedelta(days=3)))

        recently_ended_experiments = Experiment.objects.filter(
            status=Experiment.STATUS_COMPLETE).filter(
            changes__in=recent_changelog_complete)

        in_flight_experiments = Experiment.objects.filter(
            status=Experiment.STATUS_LAUNCHED
        )

        missing_dashboard_experiments = Experiment.objects.filter(
            dashboard_url__isnull=True)
        relevant_experiments = (
            recently_ended_experiments |
            missing_dashboard_experiments |
            in_flight_experiments).distinct()

        for exp in relevant_experiments:
            end_date = (None
                        if exp.end_date is None
                        else exp.end_date.strftime("%Y-%m-%d"))
            try:
                dash = StatisticalDashboard(
                  settings.REDASH_API_KEY,
                  settings.AWS_ACCESS_KEY,
                  settings.AWS_SECRET_KEY,
                  settings.S3_BUCKET_ID_STATS,
                  exp.project.name,
                  exp.name,
                  exp.slug,
                  exp.start_date.strftime("%Y-%m-%d"),
                  end_date
                )

                # This dashboard was recently updated, no need to update again.
                update_begin = dash.get_update_range().get("min", None)
                if update_begin is not None and (
                  update_begin > (datetime.now() - timedelta(days=1))):
                    continue

                dash.add_graph_templates(self.POPULATION_TEMPLATE)
                dash.add_ttable_data(
                  self.EVENTS_PER_HOUR_TEMPLATE,
                  self.UT_HOURLY_TTABLE,
                  dash.UT_HOURLY_EVENTS
                )
                dash.add_ttable(self.UT_HOURLY_TTABLE)

                exp.dashboard_url = dash.public_url
                exp.save()
            except StatisticalDashboard.ExternalAPIError as external_api_err:
                logging.error((
                  'ExternalAPIError '
                  'for {experiment}: {err}').format(
                  experiment=exp, err=external_api_err))
            except ValueError as val_err:
                logging.error((
                  'StatisticalDashboard Value Error '
                  'for {experiment}: {err}').format(
                  experiment=exp, err=val_err))

    def handle(self, *args, **options):
        self.generate_dashboards()
