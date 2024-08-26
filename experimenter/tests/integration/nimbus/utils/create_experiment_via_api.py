import sys
from pathlib import Path

here = Path(__file__)
sys.path.append(str(here.parents[2].absolute()))

import helpers

from nimbus.models.base_dataclass import BaseExperimentApplications

feature_config_id = {
    BaseExperimentApplications.FIREFOX_DESKTOP.value: helpers.get_feature_id_as_string(
        "no-feature-firefox-desktop", BaseExperimentApplications.FIREFOX_DESKTOP.value
    ),
    BaseExperimentApplications.FIREFOX_FENIX.value: helpers.get_feature_id_as_string(
        "no-feature-fenix", BaseExperimentApplications.FIREFOX_FENIX.value
    ),
    BaseExperimentApplications.FIREFOX_IOS.value: helpers.get_feature_id_as_string(
        "no-feature-ios", BaseExperimentApplications.FIREFOX_IOS.value
    ),
    BaseExperimentApplications.FOCUS_ANDROID.value: helpers.get_feature_id_as_string(
        "no-feature-focus-android", BaseExperimentApplications.FOCUS_ANDROID.value
    ),
    BaseExperimentApplications.FOCUS_IOS.value: helpers.get_feature_id_as_string(
        "no-feature-focus-ios", BaseExperimentApplications.FOCUS_IOS.value
    ),
    BaseExperimentApplications.DEMO_APP.value: helpers.get_feature_id_as_string(
        "example-feature", BaseExperimentApplications.DEMO_APP.value
    ),
}

default_data = {
    "hypothesis": "Test Hypothesis",
    "application": "FIREFOX_IOS",
    "changelogMessage": "test updates",
    "targetingConfigSlug": "no_targeting",
    "publicDescription": "Some sort of Fancy Words",
    "riskRevenue": False,
    "riskPartnerRelated": False,
    "riskBrand": False,
    "riskMessage": False,
    "featureConfigIds": [int(feature_config_id)],
    "referenceBranch": {
        "description": "reference branch",
        "name": "Branch 1",
        "ratio": 50,
        "featureValues": [
            {
                "featureConfig": str(feature_config_id),
                "value": "{}",
            },
        ],
    },
    "treatmentBranches": [],
    "populationPercent": "100",
    "totalEnrolledClients": 55,
    "firefoxMinVersion": "FIREFOX_120",
}

helpers.create_experiment("firefox ios", "FIREFOX_IOS", default_data)
