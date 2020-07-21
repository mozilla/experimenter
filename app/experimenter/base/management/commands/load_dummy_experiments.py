from typing import cast, TypedDict
import logging
import random

from django.core.management.base import CommandParser, BaseCommand

from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.models import Experiment


logger = logging.getLogger()


class Options(TypedDict):
    num_of_experiments: int
    status: str


class Command(BaseCommand):
    help = "Generates dummy experiment data"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--num_of_experiments", default=10, type=int)
        parser.add_argument(
            "--status",
            choices=[choice[0] for choice in Experiment.STATUS_CHOICES],
            help="status of experiments populated",
        )

    def handle(self, *args, **options) -> None:
        self.load_dummy_experiments(cast(Options, options))

    @staticmethod
    def load_dummy_experiments(options: Options) -> None:
        for i in range(options["num_of_experiments"]):
            random_type = random.choice(Experiment.TYPE_CHOICES)[0]
            if options["status"]:
                ExperimentFactory.create_with_status(
                    options["status"], type=random_type
                )  # type: ignore
            else:
                status = Experiment.STATUS_CHOICES[i % len(Experiment.STATUS_CHOICES)][0]
                experiment = ExperimentFactory.create_with_status(
                    status, type=random_type
                )  # type: ignore
                logger.info("Created {}: {}".format(experiment, status))
