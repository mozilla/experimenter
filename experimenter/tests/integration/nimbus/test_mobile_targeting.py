import json
from pathlib import Path

import pytest

from nimbus.jexl import collect_exprs
from nimbus.models.base_app_context_dataclass import BaseAppContextDataClass
from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.utils import helpers

nimbus_rust = pytest.importorskip("nimbus_rust")


class MockMetricsHandler(nimbus_rust.MetricsHandler):
    def __init__(self, *args, **kwargs):
        pass

    def record_enrollment_statuses(self, *args, **kwargs):
        pass

    def record_feature_activation(self, *args, **kwargs):
        pass

    def record_feature_exposure(self, *args, **kwargs):
        pass

    def record_malformed_feature_config(self, *args, **kwargs):
        pass


def client_info_list():
    with Path.open("nimbus/app_contexts.json") as file:
        return [r["app_context"] for r in json.load(file)["query_result"]["data"]["rows"]]


@pytest.fixture(params=helpers.load_targeting_configs(app="MOBILE"))
def load_app_context():
    def _load_app_context_helper(context):
        base_app_context = BaseAppContextDataClass.from_dict(context)
        return nimbus_rust.AppContext(
            app_id=base_app_context.app_id,
            app_name=base_app_context.app_name,
            channel=base_app_context.channel,
            app_version=base_app_context.app_version,
            app_build=base_app_context.app_build,
            architecture=base_app_context.architecture,
            device_manufacturer=base_app_context.device_manufacturer,
            device_model=base_app_context.device_model,
            locale=base_app_context.locale,
            os=base_app_context.os,
            os_version=base_app_context.os_version,
            android_sdk_version=base_app_context.android_sdk_version,
            debug_tag=base_app_context.debug_tag,
            installation_date=base_app_context.installation_date,
            home_directory=base_app_context.home_directory,
            custom_targeting_attributes=None,
        )

    return _load_app_context_helper


@pytest.fixture(name="sdk_client")
def fixture_sdk_client():
    def _client_helper(app_context):
        return nimbus_rust.NimbusClient(
            app_context,
            [],
            Path.cwd(),
            None,
            MockMetricsHandler(),
        )

    return _client_helper


@pytest.mark.run_targeting
@pytest.mark.parametrize("targeting", helpers.load_targeting_configs("MOBILE"))
@pytest.mark.parametrize("context", client_info_list())
def test_check_mobile_targeting(
    sdk_client,
    load_app_context,
    context,
    targeting,
    experiment_slug,
):
    # The context fixtures can only contain strings or null
    context["language"] = context["language"][:2]  # strip region
    # This context dictionary supports non string values
    # and must be encoded as JSON before being passed to the evaluator
    custom_targeting_attributes = json.dumps(
        {
            "is_already_enrolled": True,
            "days_since_update": 1,
            "days_since_install": 1,
            "isFirstRun": "true",
            "is_first_run": True,
            "is_phone": True,
            "is_review_checker_enabled": True,
        }
    )
    client = sdk_client(load_app_context(context))
    targeting_helper = client.create_targeting_helper(
        additional_context=custom_targeting_attributes
    )

    helpers.create_basic_experiment(
        experiment_slug,
        BaseExperimentApplications.FIREFOX_FENIX.value,
        targeting,
        languages=context["language"],
    )
    data = helpers.load_experiment_data(experiment_slug)
    expression = data["data"]["experimentBySlug"]["jexlTargetingExpression"]

    for sub_expr in collect_exprs(expression):
        # The evaluator will throw if it detects a syntax error, a comparison type
        # mismatch, or an undefined variable
        try:
            # Wrap the sub expression in a boolean test because the evaluator will throw
            # if the return type is not bool
            sub_expr = f"{sub_expr} == true"
            targeting_helper.eval_jexl(sub_expr)
        except Exception as e:
            raise Exception(f"Error evaluating: '{sub_expr}': {e}") from e
