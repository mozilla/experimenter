import datetime
import json


def build_analysis_json(slug, generated_at, **overrides):
    """A minimal blob conforming to the published Highwind schema."""
    metadata = {
        "schema_version": 1,
        "experiment_slug": slug,
        "as_of_date": generated_at.date().isoformat(),
        "generated_at": generated_at.isoformat(),
        "pipeline_version": "1.0.0",
        "start_date": (generated_at.date() - datetime.timedelta(days=14)).isoformat(),
        "end_date": None,
        "analysis_unit": "client_id",
        "reference_branch": "control",
        "branches": ["control", "treatment"],
    }
    return json.dumps(
        {
            "metadata": metadata,
            "segments": [],
            "metrics": [],
            "errors": [],
            **overrides,
        }
    )
