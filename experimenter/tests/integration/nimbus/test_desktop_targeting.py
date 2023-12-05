import json

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
):
    targeting = helpers.load_targeting_configs()[1]
    data = {
        "hypothesis": "Test Hypothesis",
        "application": BaseExperimentApplications.FIREFOX_DESKTOP.value,
        "changelogMessage": "test updates",
        "targetingConfigSlug": targeting,
        "publicDescription": "Some sort of Fancy Words",
        "riskRevenue": False,
        "riskPartnerRelated": False,
        "riskBrand": False,
        "featureConfigIds": [1],
        "referenceBranch": {
            "description": "reference branch",
            "name": "Branch 1",
            "ratio": 50,
            "featureValues": [
                {
                    "featureConfig": "1",
                    "value": "{}",
                },
            ],
        },
        "treatmentBranches": [
            {
                "description": "treatment branch",
                "name": "Branch 2",
                "ratio": 50,
                "featureValues": [
                    {
                        "featureConfig": "1",
                        "value": "{}",
                    },
                ],
            }
        ],
        "populationPercent": "100",
        "totalEnrolledClients": 55,
    }
    helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        data,
        targeting=targeting_config_slug,
    )
    experiment_data = helpers.load_experiment_data(experiment_slug)
    targeting = experiment_data["data"]["experimentBySlug"]["jexlTargetingExpression"]
    recipe = experiment_data["data"]["experimentBySlug"]["recipeJson"]

    # Inject filter expression
    selenium.get("about:blank")
    with open("nimbus/utils/filter_expression.js") as js:
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
    experiment_default_data,
    experiment_slug,
):
    experiment_default_data.update(audience_field)
    helpers.create_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_DESKTOP.value,
        experiment_default_data,
        targeting="no_targeting",
    )
    experiment_data = helpers.load_experiment_data(experiment_slug)
    targeting = experiment_data["data"]["experimentBySlug"]["jexlTargetingExpression"]
    recipe = experiment_data["data"]["experimentBySlug"]["recipeJson"]

    # Inject filter expression
    selenium.get("about:blank")
    with open("nimbus/utils/filter_expression.js") as js:
        result = Browser.execute_script(
            selenium,
            targeting,
            json.dumps({"experiment": recipe}),
            script=js.read(),
            context="chrome",
        )
    assert result is not None, "Invalid Targeting, or bad recipe"
