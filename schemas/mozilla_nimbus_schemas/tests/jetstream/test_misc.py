from mozilla_nimbus_schemas.jetstream import AnalysisWindow

"""
Test cases for metadata schemas:
- ExternalConfig, Metadata, Metric, Outcome
"""


def test_string_coersion():
    """Test that enum values properly coerce to strings."""
    assert AnalysisWindow.DAILY == "daily"
    test_str = f"test_{AnalysisWindow.OVERALL}"
    assert test_str == "test_overall"
