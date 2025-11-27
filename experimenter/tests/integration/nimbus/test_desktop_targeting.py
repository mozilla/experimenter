import json
import logging
import time
from functools import cache
from pathlib import Path

import pytest

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.browser import Browser
from nimbus.utils import helpers


@pytest.fixture
@cache
def filter_expression_path():
    path = Path(__file__).parent / "utils" / "filter_expression.js"
    return path.absolute()


@pytest.fixture(scope="function", autouse=True)
def setup_browser(selenium, filter_expression_path):
    """Open about:blank and initialize targeting environment once per test function."""
    selenium.get("about:blank")

    # Initialize TelemetryEnvironment and ExperimentAPI once
    with filter_expression_path.open() as js:
        result = Browser.execute_async_script(
            selenium,
            script=js.read(),
            context="chrome",
        )
    assert result is True, "Failed to initialize targeting environment"

    yield


@pytest.mark.run_targeting
def test_check_advanced_targeting(
    selenium,
    experiment_slug,
    default_data_api,
    filter_expression_path,
):
    """
    Evaluates all targeting configs in parallel using Promise.all for fast execution.
    """
    targeting_slugs = helpers.load_targeting_configs()
    targeting_tests = []

    # Create experiments for all targeting configs
    for idx, slug in enumerate(targeting_slugs):
        test_slug = f"{experiment_slug}_{idx}_{slug}"
        default_data_api["targetingConfigSlug"] = slug
        helpers.create_experiment(
            test_slug,
            BaseExperimentApplications.FIREFOX_DESKTOP.value,
            default_data_api,
            targeting=slug,
        )
        logging.info(f"Created experiment: {test_slug}")
        # Delay to prevent race conditions when creating many experiments
        time.sleep(1)

        experiment_data = helpers.load_experiment_data(test_slug)
        targeting = experiment_data["data"]["experimentBySlug"]["jexlTargetingExpression"]
        recipe = experiment_data["data"]["experimentBySlug"]["recipeJson"]

        targeting_tests.append(
            {
                "slug": slug,
                "targeting": targeting,
                "recipe": json.dumps({"experiment": recipe}),
            }
        )

    # Evaluate all targeting expressions in parallel using Promise.all
    logging.info(
        f"Evaluating {len(targeting_tests)} targeting expressions in parallel..."
    )
    with filter_expression_path.open() as js:
        results = Browser.execute_async_script(
            selenium,
            json.dumps(targeting_tests),
            script=js.read(),
            context="chrome",
        )

    # Validate results
    assert results is not None, "Failed to evaluate targeting expressions"
    assert len(results) == len(targeting_slugs), (
        f"Expected {len(targeting_slugs)} results, got {len(results)}"
    )

    # Report any failures
    failed_tests = []
    for result in results:
        logging.info(
            f"Slug: {result['slug']}, "
            f"Result: {result.get('result')}, "
            f"Error: {result.get('error')}"
        )
        if result.get("result") is None:
            error_msg = result.get("error", "Unknown error")
            failed_tests.append(f"{result['slug']}: {error_msg}")

    if failed_tests:
        pytest.fail("Failed targeting evaluations:\n" + "\n".join(failed_tests))


@pytest.mark.parametrize(
    "audience_field",
    [
        {"channel": "NIGHTLY"},
        {"firefoxMinVersion": "FIREFOX_100"},
        {"firefoxMaxVersion": "FIREFOX_120"},
        {"locales": [37]},
        {"countries": [42]},
        {"proposedEnrollment": "14"},
        {"proposedDuration": "30"},
    ],
    ids=[
        "channel",
        "min_version",
        "max_version",
        "locales",
        "countries",
        "proposed_enrollment",
        "proposed_duration",
    ],
)
@pytest.mark.run_targeting
def test_check_audience_targeting(
    selenium,
    audience_field,
    experiment_slug,
    default_data_api,
    filter_expression_path,
):
    """Evaluates single audience targeting configuration."""
    default_data_api.update(audience_field)
    experiment = helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        default_data_api,
        targeting="no_targeting",
    )
    logging.info(f"GraphQL creation: {experiment}")
    experiment_data = helpers.load_experiment_data(experiment_slug)
    targeting = experiment_data["data"]["experimentBySlug"]["jexlTargetingExpression"]
    logging.info(f"Experiment Targeting: {targeting}")
    recipe = experiment_data["data"]["experimentBySlug"]["recipeJson"]
    logging.info(f"Experiment Recipe: {recipe}")

    # Use parallel mode with single item for consistency
    targeting_tests = [
        {
            "slug": audience_field,
            "targeting": targeting,
            "recipe": json.dumps({"experiment": recipe}),
        }
    ]

    with filter_expression_path.open() as js:
        results = Browser.execute_async_script(
            selenium,
            json.dumps(targeting_tests),
            script=js.read(),
            context="chrome",
        )

    assert results is not None and len(results) == 1, "Failed to evaluate targeting"
    assert results[0].get("result") is not None, (
        f"Invalid Targeting: {results[0].get('error', 'unknown error')}"
    )
