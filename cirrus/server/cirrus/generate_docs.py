import argparse
import json
import os
import sys

from fastapi.openapi.utils import get_openapi
from main import app

DOCS_DIR = "cirrus/server/cirrus/docs"
OPENAPI_PATH = os.path.join(DOCS_DIR, "openapi.json")


def generate_or_check_openapi(check_docs: bool) -> None:
    # Generate new OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    if check_docs:
        # Check if openapi.json is up-to-date
        try:
            with open(OPENAPI_PATH, "r") as f:
                if openapi_schema != json.load(f):
                    print("openapi.json is not up-to-date.")
                    print("Please update the docs using `make cirrus_generate_docs`.")
                    sys.exit(1)
                else:
                    print("openapi.json is already up-to-date.")
        except FileNotFoundError:
            print("openapi.json not found.")
            print("Please generate the docs using `make cirrus_generate_docs`.")
            sys.exit(1)
    else:
        # Update openapi.json
        with open(OPENAPI_PATH, "w") as f:
            json.dump(openapi_schema, f)
        print("openapi.json has been updated!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates OpenAPI schema")
    parser.add_argument(
        "--check",
        dest="check_docs",
        action="store_true",
        help="Check if openapi.json is up-to-date",
    )
    args = parser.parse_args()

    generate_or_check_openapi(args.check_docs)
