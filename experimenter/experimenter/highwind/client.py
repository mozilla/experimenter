import importlib.metadata
import json
import logging

from django.core.files.storage import storages
from mozilla_nimbus_schemas.highwind import HighwindAnalysis

logger = logging.getLogger(__name__)

analysis_storage = storages["analysis"]

# The Highwind job writes to gs://mozanalysis/highwind, the bucket Jetstream's results and
# the enrollment funnel already come from, so the analysis storage reaches it with only a
# prefix added.
BLOB_PREFIX = "highwind"

# The job stamps every blob with its own installed mozilla-nimbus-schemas version, so a
# blob declaring anything else was written against a different release and cannot be read
# here. Taking the value from the installed package rather than hardcoding it means this
# does not need revisiting on the next release.
SCHEMA_VERSION = importlib.metadata.version("mozilla-nimbus-schemas")


class UnsupportedSchemaError(Exception):
    """A blob written against a schema this does not know how to read."""


def blob_path(slug):
    """The object name the Highwind job writes one experiment's results under.

    Underscores rather than the hyphens a slug carries, matching the naming of the other
    artifacts the bucket holds.
    """
    return f"{BLOB_PREFIX}/{slug.replace('-', '_')}.json"


def list_analysis_blobs():
    """Every object the job has written under the prefix, as one listing per run."""
    _, filenames = analysis_storage.listdir(BLOB_PREFIX)
    return {f"{BLOB_PREFIX}/{filename}" for filename in filenames}


def get_analysis(experiment):
    """The experiment's published analysis, or None if the job has not written one.

    Raises UnsupportedSchemaError for a blob that does not claim the version we read,
    and ValidationError for one that claims it but does not conform. The caller leaves the
    stored analysis alone either way, and only the second is worth reporting: a blob the
    job will never rewrite cannot be fixed by looking at it again next hour.
    """
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
