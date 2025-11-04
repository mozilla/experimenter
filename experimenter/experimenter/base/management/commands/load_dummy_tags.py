import logging

from django.core.management.base import BaseCommand

from experimenter.experiments.tests.factories import TagFactory

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Generates dummy tags"

    def handle(self, *args, **options):
        for _ in range(8):
            tag = TagFactory.create()
            logger.info(f"Created tag: {tag.name} ({tag.color})")
