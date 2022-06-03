import json
import os
from pathlib import Path

import pytest
from nimbus.models.base_app_context_dataclass import BaseAppContextDataClass
from nimbus.utils import helpers

nimbus = pytest.importorskip("nimbus_rust")


def locale_number_loader(locales=None):
    locale_list = []
    path = Path().resolve()
    path = str(path)
    path = path.strip("/tests/integration/nimbus")
    path = f"/{path}/experimenter/base/fixtures/locales.json"
    with open(path) as file:
        data = json.loads(file.read())
        for locale in locales:
            for item in data:
                if locale in item["fields"]["code"][:2]:
                    locale_list.append(item["pk"])
    return locale_list


def client_info_list():
    with open("nimbus/app_contexts.json") as file:
        return json.load(file)["query_result"]["data"]["rows"]


@pytest.fixture
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
    return nimbus.AvailableRandomizationUnits(None, 0)


@pytest.fixture(name="sdk_client")
def fixture_sdk_client(ar_units):
    def _client_helper(app_context):
        return nimbus.NimbusClient(app_context, os.getcwd(), None, ar_units)

    return _client_helper


@pytest.fixture(name="jexl_evaluator")
def fixture_jexl_evaluator():
    def _eval_jexl(sdk_client, expression):
        targetting_helper = sdk_client.create_targeting_helper()
        try:
            value = targetting_helper.eval_jexl(expression)
        except nimbus.NimbusError.EvaluationError:
            return None
        else:
            return value

    return _eval_jexl


@pytest.mark.parametrize("context", client_info_list())
@pytest.mark.run_targeting
def test_check_mobile_targeting(
    jexl_evaluator, sdk_client, load_app_context, context, slugify, experiment_name
):
    context = json.loads(context["app_context"])
    context["locale"] = context["locale"][:2]  # strip region
    helpers.create_mobile_experiment(
        slugify(experiment_name),
        context["app_name"],
        locale_number_loader([context["locale"]]),
    )
    data = helpers.load_experiment_data(slugify(experiment_name))
    expression = data["data"]["experimentBySlug"]["jexlTargetingExpression"]
    assert jexl_evaluator(sdk_client(load_app_context(context)), expression)


@pytest.mark.parametrize("context", client_info_list())
@pytest.mark.run_targeting
def test_check_mobile_targeting_falsey(
    jexl_evaluator, sdk_client, load_app_context, context, slugify, experiment_name
):
    context = json.loads(context["app_context"])
    helpers.create_mobile_experiment(
        slugify(experiment_name),
        context["app_name"],
        locale_number_loader([context["locale"][:2]]),
    )
    expression = "'zz' in locale"  # represents a malformed jexl expression
    assert jexl_evaluator(sdk_client(load_app_context(context)), expression) is False


@pytest.mark.run_targeting
def test_check_mobile_targeting_undefined(
    jexl_evaluator, sdk_client, load_app_context, slugify, experiment_name
):
    client = json.loads(client_info_list()[0]["app_context"])
    helpers.create_mobile_experiment(
        slugify(experiment_name),
        client["app_name"],
        locale_number_loader([client["locale"]]),
    )
    expression = ""  # represents a malformed jexl expression
    assert jexl_evaluator(sdk_client(load_app_context(client)), expression) is None
