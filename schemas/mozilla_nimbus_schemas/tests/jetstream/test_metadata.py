import datetime as dt

from mozilla_nimbus_schemas.jetstream import Metadata

"""
Test cases for metadata schemas:
- ExternalConfig, Metadata, Metric, Outcome
"""


def test_parse_metadata():
    """Test the custom json.loads functionality"""
    metadata_json = """
        {
            "analysis_start_time": "2023-05-01 01:02:03.000000+00:00",
            "external_config": {
                "reference_branch": "test-branch",
                "end_date": null,
                "start_date": "2023-05-15",
                "enrollment_period": 14,
                "skip": false,
                "url": "https://example.com/test/config"
            },
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
            "outcomes": {
                "test_outcome": {
                    "commit_hash": "abcd1234",
                    "default_metrics": ["test-metric1"],
                    "description": "outcome for \n testing",
                    "friendly_name": "Test Outcome",
                    "metrics": ["test-metric1", "test-metric2"],
                    "slug": "test-outcome"
                }
            },
            "schema_version": 4
        }
    """
    metadata = Metadata.parse_raw(metadata_json)
    assert metadata.external_config is not None
    assert not metadata.external_config.skip
    assert metadata.outcomes != {}
    assert metadata.outcomes.get("test_outcome").slug == "test-outcome"
    assert metadata.schema_version == 4
    assert metadata.analysis_start_time == dt.datetime(
        2023, 5, 1, 1, 2, 3, tzinfo=dt.timezone.utc
    )
