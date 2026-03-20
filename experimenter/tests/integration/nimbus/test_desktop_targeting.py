import json
import uuid
from functools import cache
from pathlib import Path

import pytest

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.browser import Browser
from nimbus.utils import helpers


@pytest.fixture(scope="module")
def base_experiment_slug():
    """Create one experiment per module that gets reused for all targeting tests."""
    name = f"targeting-test-base-{uuid.uuid4().hex[:8]}"
    slug = helpers.create_basic_experiment(
        name,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
    )
    return slug


@pytest.fixture(params=helpers.load_targeting_configs())
def targeting_config_slug(request):
    return request.param


@pytest.fixture
@cache
def targeting_script():
    path = Path(__file__).parent / "utils" / "filter_expression.js"
    with path.open() as f:
        return f.read()


@pytest.mark.parametrize("application", ["firefox-desktop"], ids=["FIREFOX_DESKTOP"])
@pytest.mark.run_targeting
def test_check_advanced_targeting(
    driver,
    application,
    base_experiment_slug,
    targeting_config_slug,
    targeting_script,
):
    helpers.update_experiment_audience(
        base_experiment_slug,
        {"targeting_config_slug": targeting_config_slug},
    )
    experiment_data = helpers.load_experiment_data(base_experiment_slug)
    targeting = experiment_data["targeting"]
    recipe = experiment_data["recipe_json"]

    result = Browser.execute_async_script(
        driver,
        targeting,
        json.dumps({"experiment": recipe}),
        script=targeting_script,
        context="chrome",
    )
    assert result is not None, "Invalid Targeting, or bad recipe"


@pytest.mark.parametrize(
    "audience_field",
    [
        {"channel": "nightly"},
        {"firefox_min_version": "100.!"},
        {"firefox_max_version": "120.!"},
        {"locales": [37]},
        {"countries": [42]},
        {"proposed_enrollment": "14"},
        {"proposed_duration": "30"},
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
    targeting_script,
):
    helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        audience_field,
    )
    experiment_data = helpers.load_experiment_data(experiment_slug)
    targeting = experiment_data["targeting"]
    recipe = experiment_data["recipe_json"]

    result = Browser.execute_async_script(
        selenium,
        targeting,
        json.dumps({"experiment": recipe}),
        script=targeting_script,
        context="chrome",
    )
    assert result is not None, "Invalid Targeting, or bad recipe"
