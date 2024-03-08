import json
from pathlib import Path

import pytest

from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.pages.browser import Browser
from nimbus.utils import helpers


@pytest.fixture(params=helpers.load_targeting_configs())
def targeting_config_slug(request):
    return request.param


@pytest.mark.run_targeting
def test_check_advanced_targeting(
    selenium,
    targeting_config_slug,
    experiment_slug,
    default_data_api,
):
    helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        default_data_api,
        targeting=targeting_config_slug,
    )
    experiment_data = helpers.load_experiment_data(experiment_slug)
    targeting = experiment_data["data"]["experimentBySlug"]["jexlTargetingExpression"]
    recipe = experiment_data["data"]["experimentBySlug"]["recipeJson"]

    # Inject filter expression
    selenium.get("about:blank")
    with Path("nimbus", "utils", "filter_expression.js").open() as js:
        result = Browser.execute_script(
            selenium,
            targeting,
            json.dumps({"experiment": recipe}),
            script=js.read(),
            context="chrome",
        )
    assert result is not None, "Invalid Targeting, or bad recipe"


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
):
    default_data_api.update(audience_field)
    helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        default_data_api,
        targeting="no_targeting",
    )
    experiment_data = helpers.load_experiment_data(experiment_slug)
    targeting = experiment_data["data"]["experimentBySlug"]["jexlTargetingExpression"]
    recipe = experiment_data["data"]["experimentBySlug"]["recipeJson"]

    # Inject filter expression
    selenium.get("about:blank")
    with Path("nimbus", "utils", "filter_expression.js").open() as js:
        result = Browser.execute_script(
            selenium,
            targeting,
            json.dumps({"experiment": recipe}),
            script=js.read(),
            context="chrome",
        )
    assert result is not None, "Invalid Targeting, or bad recipe"
