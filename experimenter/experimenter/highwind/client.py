import logging

from django.core.files.storage import storages
from mozilla_nimbus_schemas.highwind import HighwindAnalysis

logger = logging.getLogger(__name__)

analysis_storage = storages["analysis"]

# The Highwind job writes to gs://mozanalysis/highwind, the bucket Jetstream's results and
# the enrollment funnel already come from, so the analysis storage reaches it with only a
# prefix added.
BLOB_PREFIX = "highwind"


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

    Raises ValidationError if the blob does not conform to the published schema, which the
    caller treats as a reason to leave the stored analysis alone rather than overwrite it.
    """
    path = blob_path(experiment.slug)

    if not analysis_storage.exists(path):
        return None

    with analysis_storage.open(path) as blob:
        return HighwindAnalysis.model_validate_json(blob.read())
