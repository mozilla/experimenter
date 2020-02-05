import logging
import random
import json

from django.core.management import call_command
import io
import codecs
from django.template.loader import render_to_string
from django.core.management.base import BaseCommand

from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.models import Experiment


logger = logging.getLogger()


class Command(BaseCommand):
    help = "Generates API docs"

    def add_arguments(self, parser):
        parser.add_argument("--check", default=False, type=bool)

    def handle(self, *args, **options):
        self.generate_docs(options)

    @staticmethod
    def generate_docs(options):
        if options["check"]:
            output = io.StringIO()
            call_command("generateschema", "--format=openapi-json", stdout=output)
            output.seek(0)
            api_json = output.read()

            with open("/app/experimenter/docs/openapi-schema.json", "r") as f:
                old_json = f.read()
                if json.loads(api_json) != json.loads(old_json):
                    raise ValueError("Api Schemas have changed and have not been updated")

        else:
            output = io.StringIO()
            call_command("generateschema", "--format=openapi-json", stdout=output)
            output.seek(0)
            api_json = output.read()

            doc_rendered = render_to_string(
                "swagger-ui-template.html", context={"spec": api_json}
            )

            with open("/app/experimenter/docs/openapi-schema.json", "w+") as f:
                f.write(api_json)
                f.close()
            with open("/app/experimenter/docs/swagger-ui.html", "w+") as f:
                f.write(doc_rendered)
                f.close()
                logger.info("Docs generated Successfully")
