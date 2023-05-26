import datetime as dt
import json

import pytest
from pydantic import ValidationError

from mozilla_nimbus_schemas.jetstream import ExternalConfig, Metadata, Metric, Outcome

"""
Test cases for metadata schemas:
- ExternalConfig, Metadata, Metric, Outcome
"""


def test_empty_metadata_types_fail():
    with pytest.raises(ValidationError):
        _ = Metadata()
    with pytest.raises(ValidationError):
        _ = Metric()
    with pytest.raises(ValidationError):
        _ = Outcome()
    with pytest.raises(ValidationError):
        _ = ExternalConfig()


def test_basic_external_config():
    ec = ExternalConfig(url="http://example.com/external/config")
    assert ec.url == "http://example.com/external/config"
    assert ec.skip is None
    test_json_str = """{
        "url": "http://example.com/external/config"
    }"""
    ec_test = ExternalConfig.parse_raw(test_json_str)
    assert ec == ec_test


def test_basic_outcome():
    outcome = Outcome(
        commit_hash="abcd1234",
        default_metrics=["test-metric1"],
        description="outcome for testing",
        friendly_name="Test Outcome",
        metrics=["test-metric1", "test-metric2"],
        slug="test-outcome",
    )
    assert outcome.slug == "test-outcome"
    assert len(outcome.metrics) == 2
    outcome_json = outcome.json()
    test_json_str = """{
        "commit_hash": "abcd1234",
        "default_metrics": ["test-metric1"],
        "description": "outcome for testing",
        "friendly_name": "Test Outcome",
        "metrics": ["test-metric1", "test-metric2"],
        "slug": "test-outcome"
    }"""
    assert json.loads(outcome_json) == json.loads(test_json_str)


def test_parse_metadata():
    metadata_json = """
        {
            "analysis_start_time": "2023-05-01 01:02:03.000000+00:00",
            "external_config": null,
            "metrics": {
                "active_hours": {
                    "analysis_bases": [
                        "enrollments",
                        "exposures"
                    ],
                    "bigger_is_better": true,
                    "description": "Measures the amount of time\n",
                    "friendly_name": "Active hours"
                },
                "ad_clicks": {
                    "analysis_bases": [
                        "enrollments",
                        "exposures"
                    ],
                    "bigger_is_better": true,
                    "description": "Counts clicks on ads\n",
                    "friendly_name": "Ad clicks"
                }
            },
            "outcomes": {},
            "schema_version": 4
        }
    """
    metadata = Metadata.parse_raw(metadata_json)
    assert metadata.external_config is None
    assert metadata.schema_version == 4
    assert metadata.analysis_start_time == dt.datetime(
        2023, 5, 1, 1, 2, 3, tzinfo=dt.timezone.utc
    )


def test_parse_metadata_fails():
    stat_json = """
        {
            "analysis_start_time": "2023-05-01 01:02:03.000000+00:00",
            "external_config": null,
            "metrics": null,
            "outcomes": {},
            "schema_version": 4
        }
    """
    with pytest.raises(ValidationError):
        Metadata.parse_raw(stat_json)
