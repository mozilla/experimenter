import logging
import random

from django.core.management.base import BaseCommand

from experimenter.experiments.models import Experiment
from experimenter.experiments.models.nimbus import NimbusExperiment
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    NimbusExperimentFactory,
)

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Generates dummy experiment data"

    def handle(self, *args, **options):
        for status, _ in Experiment.STATUS_CHOICES:
            random_type = random.choice(Experiment.TYPE_CHOICES)[0]
            experiment = ExperimentFactory.create_with_status(status, type=random_type)
            logger.info("Created {}: {}".format(experiment, status))

        for status, _ in NimbusExperiment.Status.choices:
            experiment = NimbusExperimentFactory.create_with_status(status)
            logger.info("Created {}: {}".format(experiment, status))
