import logging

from django.core.management.base import BaseCommand

from experimenter.projects.tests.factories import ProjectFactory

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Generates dummy project data"

    def handle(self, *args, **options):
        for _ in range(3):
            ProjectFactory.create()
