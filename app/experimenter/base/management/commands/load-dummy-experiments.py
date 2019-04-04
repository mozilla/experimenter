from django.core.management.base import BaseCommand
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.models import Experiment
import random


class Command(BaseCommand):
    help = "Generates dummy experiment data"

    def add_arguments(self, parser):
        parser.add_argument("--num_of_experiments", default=10, type=int)
        parser.add_argument(
            "--status",
            choices=[choice[0] for choice in Experiment.STATUS_CHOICES],
            help="status of experiments populated",
        )

    def handle(self, *args, **options):
        self.load_dummy_experiments(options)

    @staticmethod
    def load_dummy_experiments(options):
        for i in range(options["num_of_experiments"]):
            random_type = random.choice(Experiment.TYPE_CHOICES)[0]
            if options["status"]:
                ExperimentFactory.create_with_status(
                    options["status"], type=random_type
                )
            else:
                random_status = random.choice(Experiment.STATUS_CHOICES)[0]
                ExperimentFactory.create_with_status(
                    random_status, type=random_type
                )
