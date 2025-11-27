import json
import logging
from functools import cache
from pathlib import Path

import pytest

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.browser import Browser
from nimbus.utils import helpers


def get_desktop_targeting_configs():
    """Get all targeting configs with expressions for desktop."""
    return helpers.load_targeting_configs_with_expressions(
        BaseExperimentApplications.FIREFOX_DESKTOP.value
    )


@pytest.fixture
@cache
def filter_expression_path():
    path = Path(__file__).parent / "utils" / "filter_expression.js"
    return path.absolute()


@pytest.fixture(scope="function", autouse=True)
def setup_browser(selenium):
    """Open about:blank once per test function."""
    selenium.get("about:blank")
    yield


@pytest.mark.run_targeting
def test_check_advanced_targeting(
    selenium,
    filter_expression_path,
):
    """Test all targeting expressions in parallel without creating experiments."""
    # Get all desktop targeting configs
    targeting_configs = get_desktop_targeting_configs()

    # Use a minimal valid recipe
    recipe = {
        "id": "test-experiment",
        "slug": "test-experiment",
        "appName": "firefox_desktop",
        "appId": "firefox-desktop",
        "channel": "nightly",
        "userFacingName": "Test Experiment",
        "userFacingDescription": "Test",
        "isEnrollmentPaused": False,
        "bucketConfig": {
            "randomizationUnit": "normandy_id",
            "namespace": "test",
            "start": 0,
            "count": 1000,
            "total": 10000,
        },
        "branches": [
            {
                "slug": "control",
                "ratio": 1,
            }
        ],
        "startDate": None,
        "endDate": None,
        "proposedEnrollment": 7,
        "referenceBranch": "control",
        "featureIds": [],
    }

    # Build array of targeting tests for parallel evaluation
    targeting_tests = [
        {
            "slug": config["value"],
            "targeting": config["targeting"],
            "recipe": recipe,
        }
        for config in targeting_configs
    ]

    logging.info(
        f"Evaluating {len(targeting_tests)} targeting expressions in parallel..."
    )

    # Evaluate all targeting expressions in parallel
    with filter_expression_path.open() as js:
        results = Browser.execute_async_script(
            selenium,
            json.dumps(targeting_tests),
            script=js.read(),
            context="chrome",
        )

    # Validate results
    assert results is not None, "Failed to evaluate targeting expressions"
    assert len(results) == len(targeting_configs), (
        f"Expected {len(targeting_configs)} results, got {len(results)}"
    )

    # Report results and collect failures
    failed_tests = []
    for result in results:
        slug = result.get("slug", "unknown")
        success = result.get("result")
        error = result.get("error")

        if success is not None:
            logging.info(f"✓ {slug}: PASS")
        else:
            logging.error(f"✗ {slug}: FAIL - {error}")
            failed_tests.append(f"{slug}: {error}")

    # Fail the test if any targeting expressions failed
    if failed_tests:
        pytest.fail(
            f"Failed targeting evaluations ({len(failed_tests)}/{len(results)}):\n"
            + "\n".join(failed_tests)
        )


@pytest.mark.run_targeting
def test_check_audience_targeting(
    selenium,
    filter_expression_path,
):
    """Test that audience fields generate valid targeting expressions."""
    # These tests verify the targeting expression generation logic
    # without needing to create actual experiments
    recipe = {
        "id": "test-experiment",
        "slug": "test-experiment",
        "appName": "firefox_desktop",
        "appId": "firefox-desktop",
        "channel": "nightly",
        "userFacingName": "Test Experiment",
        "userFacingDescription": "Test",
        "isEnrollmentPaused": False,
        "bucketConfig": {
            "randomizationUnit": "normandy_id",
            "namespace": "test",
            "start": 0,
            "count": 1000,
            "total": 10000,
        },
        "branches": [
            {
                "slug": "control",
                "ratio": 1,
            }
        ],
        "startDate": None,
        "endDate": None,
        "proposedEnrollment": 7,
        "referenceBranch": "control",
        "featureIds": [],
    }

    audience_fields = [
        "channel",
        "min_version",
        "max_version",
        "locales",
        "countries",
        "proposed_enrollment",
        "proposed_duration",
    ]

    # Build array of audience tests for parallel evaluation
    targeting_tests = [
        {
            "slug": field,
            "targeting": "",  # Empty targeting for audience fields
            "recipe": recipe,
        }
        for field in audience_fields
    ]

    logging.info(f"Evaluating {len(targeting_tests)} audience fields in parallel...")

    # Evaluate all in parallel
    with filter_expression_path.open() as js:
        results = Browser.execute_async_script(
            selenium,
            json.dumps(targeting_tests),
            script=js.read(),
            context="chrome",
        )

    # Validate results
    assert results is not None, "Failed to evaluate audience targeting"
    assert len(results) == len(audience_fields), (
        f"Expected {len(audience_fields)} results, got {len(results)}"
    )

    # Check for failures
    failed_tests = []
    for result in results:
        slug = result.get("slug", "unknown")
        success = result.get("result")
        error = result.get("error")

        if success is not None:
            logging.info(f"✓ {slug}: PASS")
        else:
            logging.error(f"✗ {slug}: FAIL - {error}")
            failed_tests.append(f"{slug}: {error}")

    if failed_tests:
        pytest.fail(
            f"Failed audience field evaluations ({len(failed_tests)}/{len(results)}):\n"
            + "\n".join(failed_tests)
        )
