import json
import os
from pathlib import Path

import pytest
from nimbus.models.base_app_context_dataclass import BaseAppContextDataClass
from nimbus.utils import helpers

nimbus = pytest.importorskip("nimbus_rust")


def locale_database_id_loader(locales=None):
    locale_list = []
    path = Path().resolve()
    path = str(path)
    path = path.strip("/tests/integration/nimbus")
    path = os.path.join("/", path, "experimenter/base/fixtures/locales.json")
    with open(path) as file:
        data = json.loads(file.read())
        for locale in locales:
            for item in data:
                if locale in item["fields"]["code"][:2]:
                    locale_list.append(item["pk"])
    return locale_list


def client_info_list():
    with open("nimbus/app_contexts.json") as file:
        return [r["app_context"] for r in json.load(file)["query_result"]["data"]["rows"]]


@pytest.fixture(params=helpers.load_targeting_configs(app="MOBILE"))
def load_app_context():
    def _load_app_context_helper(context):
        base_app_context = BaseAppContextDataClass.from_dict(context)
        return nimbus.AppContext(
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
            custom_targeting_attributes=base_app_context.custom_targeting_attributes,
        )

    return _load_app_context_helper


@pytest.fixture(name="ar_units")
def fixture_ar_units():
    """Available Randomization Units"""
    return nimbus.AvailableRandomizationUnits(None, 0)


@pytest.fixture(name="sdk_client")
def fixture_sdk_client(ar_units):
    def _client_helper(app_context):
        return nimbus.NimbusClient(app_context, os.getcwd(), None, ar_units)

    return _client_helper


@pytest.mark.run_targeting
@pytest.mark.parametrize("targeting", helpers.load_targeting_configs("MOBILE"))
@pytest.mark.parametrize("context", client_info_list())
def test_check_mobile_targeting(
    sdk_client,
    load_app_context,
    context,
    slugify,
    experiment_name,
    create_mobile_experiment,
    targeting,
):
    # The context fixtures can only contain strings or null
    context["locale"] = context["locale"][:2]  # strip region
    # This context dictionary supports non string values
    # and must be encoded as JSON before being passed to the evaluator
    custom_targeting_attributes = json.dumps(
        {"is_already_enrolled": True, "days_since_update": 1, "days_since_install": 1}
    )
    client = sdk_client(load_app_context(context))
    targeting_helper = client.create_targeting_helper(
        additional_context=custom_targeting_attributes
    )

    experiment_slug = str(slugify(experiment_name))
    create_mobile_experiment(
        experiment_slug,
        context["app_name"],
        locale_database_id_loader([context["locale"]]),
        targeting,
    )
    data = helpers.load_experiment_data(experiment_slug)
    expression = data["data"]["experimentBySlug"]["jexlTargetingExpression"]

    # The evaluator will throw if it detects a syntax error, a comparison type mismatch,
    # or an undefined variable
    targeting_helper.eval_jexl(expression)
