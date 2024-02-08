import json
import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from rest_framework.schemas.openapi import SchemaGenerator

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Generates API docs"

    def add_arguments(self, parser):
        parser.add_argument("--check", default=False, type=bool)

    def handle(self, *args, **options):
        self.generate_docs(options)

    @staticmethod
    def generateSchema():
        generator = SchemaGenerator(title="Experimenter API")
        schema = generator.get_schema()
        paths = schema.get("paths") or []
        for path in paths:
            if "/api/v1/" in path:
                for method in paths[path]:
                    paths[path][method]["tags"] = ["Core: Public"]
            elif "/api/v2/" in path:
                for method in paths[path]:
                    paths[path][method]["tags"] = ["Core: Private"]
            elif "/api/v6/" in path:
                for method in paths[path]:
                    paths[path][method]["tags"] = ["Nimbus: Public"]

        return json.dumps(schema, indent=2)

    @staticmethod
    def generate_docs(options):
        api_json = Command.generateSchema()
        docs_dir = Path(settings.BASE_DIR) / "docs"
        schema_json_path = Path(docs_dir) / "openapi-schema.json"
        swagger_html_path = Path(docs_dir) / "swagger-ui.html"

        if options["check"]:
            with Path.open(schema_json_path) as f:
                old_json = f.read()
                if json.loads(api_json) != json.loads(old_json):
                    raise ValueError("Api Schemas have changed and have not been updated")

        else:
            doc_rendered = render_to_string(
                "swagger-ui-template.html", context={"spec": api_json}
            )

            with Path.open(schema_json_path, "w+") as f:
                f.write(api_json)
            with Path.open(swagger_html_path, "w+") as f:
                f.write(doc_rendered)
                logger.info("Docs generated Successfully")
