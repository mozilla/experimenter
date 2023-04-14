import json
import os

from fastapi.openapi.utils import get_openapi
from main import app

DOCS_DIR = "cirrus/server/cirrus/docs"
OPENAPI_PATH = os.path.join(DOCS_DIR, "openapi.json")


def generate_openapi_schema():
    # Generate new OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    with open(OPENAPI_PATH, "r") as f:
        if not os.path.isfile(OPENAPI_PATH) or openapi_schema != json.load(f):
            with open(OPENAPI_PATH, "w") as f:
                json.dump(openapi_schema, f)
            print("openapi.json has been updated!")
            return False
        else:
            print("openapi.json is already up-to-date.")
            return False


if __name__ == "__main__":
    generate_openapi_schema()
