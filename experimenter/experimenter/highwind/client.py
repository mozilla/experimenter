import importlib.metadata
import json
import logging

from django.core.files.storage import storages
from mozilla_nimbus_schemas.highwind import HighwindAnalysis

logger = logging.getLogger(__name__)

analysis_storage = storages["analysis"]

# Jetstream's results and the enrollment funnel already come from this bucket, so the
# analysis storage reaches the Highwind blobs with only a prefix added.
BLOB_PREFIX = "highwind"

# Read from the installed package, the same source the job stamps blobs from, so a new
# release needs no change here.
SCHEMA_VERSION = importlib.metadata.version("mozilla-nimbus-schemas")


class UnsupportedSchemaError(Exception):
    pass


def blob_path(slug):
    # Underscores rather than the hyphens a slug carries, matching the bucket's other
    # artifacts.
    return f"{BLOB_PREFIX}/{slug.replace('-', '_')}.json"


def list_analysis_blobs():
    _, filenames = analysis_storage.listdir(BLOB_PREFIX)
    return {f"{BLOB_PREFIX}/{filename}" for filename in filenames}


def get_analysis(experiment):
    # A blob declaring another version raises UnsupportedSchemaError; one declaring ours
    # that does not conform raises ValidationError. Only the second is worth reporting,
    # since a blob the job will never rewrite cannot be fixed by reading it again.
    path = blob_path(experiment.slug)

    if not analysis_storage.exists(path):
        return None

    with analysis_storage.open(path) as blob:
        payload = json.load(blob)

    metadata = payload.get("metadata") if isinstance(payload, dict) else None
    schema_version = (
        metadata.get("schema_version") if isinstance(metadata, dict) else None
    )
    if schema_version != SCHEMA_VERSION:
        raise UnsupportedSchemaError(
            f"{path} declares schema version {schema_version!r},"
            f" and this reads version {SCHEMA_VERSION}"
        )

    return HighwindAnalysis.model_validate(payload)
