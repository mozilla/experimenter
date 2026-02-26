import json
from pathlib import Path

import pytest

from nimbus.jexl import collect_exprs
from nimbus.models.base_app_context_dataclass import BaseAppContextDataClass
from nimbus.models.base_dataclass import BaseExperimentApplications
from nimbus.utils import helpers

nimbus_rust = pytest.importorskip("nimbus_megazord.nimbus")


class MockMetricsHandler(nimbus_rust.MetricsHandler):
    def __init__(self, *args, **kwargs):
        pass

    def record_database_load(self, *args, **kwargs):
        pass

    def record_database_migration(self, *args, **kwargs):
        pass

    def record_enrollment_statuses(self, *args, **kwargs):
        pass

    def record_feature_activation(self, *args, **kwargs):
        pass

    def record_feature_exposure(self, *args, **kwargs):
        pass

    def record_malformed_feature_config(self, *args, **kwargs):
        pass


def load_app_context_data():
    path = Path(__file__).parent / "app_contexts.json"
    with path.open() as file:
        return json.load(file)


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
            custom_targeting_attributes=None,
        )

    return _load_app_context_helper


@pytest.fixture(name="sdk_client")
def fixture_sdk_client():
    def _client_helper(app_context):
        return nimbus_rust.NimbusClient(
            app_context, None, [], str(Path.cwd()), MockMetricsHandler(), None, None
        )

    return _client_helper


@pytest.mark.run_targeting
@pytest.mark.parametrize("targeting", helpers.load_targeting_configs("MOBILE"))
def test_check_mobile_targeting(
    sdk_client,
    load_app_context,
    targeting,
    experiment_slug,
):
    context = load_app_context_data()
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
            "is_default_browser": True,
            "is_bottom_toolbar_user": True,
            "has_enabled_tips_notifications": True,
            "has_accepted_terms_of_use": True,
            "tou_experience_points": 0,
            "is_apple_intelligence_available": True,
            "cannot_use_apple_intelligence": True,
            "install_referrer_response_utm_source": "test",
            "number_of_app_launches": 1,
            "is_large_device": True,
            "user_accepted_tou": True,
            "no_shortcuts_or_stories_opt_outs": True,
            "addon_ids": [
                "uBlock0@raymondhill.net",
                "{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}",
                "adguardadblocker@adguard.com",
                "adblockultimate@adblockultimate.net",
                "firefox@ghostery.com",
                "lock@adblock",
                "ultrablock-pro@ultrablock.com",
                "{2b3f2f5d-f5ae-44b3-846e-b630acf8eced}",
                "kolesin.work@gmail.com",
                "adblocker@pcmatic.com",
                "{73a6fe31-595d-460b-a920-fcc0f8843232}",
            ],
            "tou_points": 3,
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
