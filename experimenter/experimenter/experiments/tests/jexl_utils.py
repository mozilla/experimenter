import json
from pathlib import Path
from unittest import mock

from nimbus_megazord import nimbus as nimbus_rust

from experimenter.experiments.constants import Application
from experimenter.experiments.jexl_utils import JEXLParser


def validate_jexl_expr(expression, application):
    JEXLParser().parse(expression)

    if application != Application.DESKTOP:
        app_context = nimbus_rust.AppContext(
            app_id="org.mozilla.firefox",
            app_name="fenix",
            channel="nightly",
            app_version="100.0",
            app_build="1",
            architecture="arm64",
            device_manufacturer="Google",
            device_model="Pixel",
            locale="en-US",
            os="Android",
            os_version="13",
            android_sdk_version="33",
            debug_tag="",
            installation_date=None,
            custom_targeting_attributes=None,
        )

        client = nimbus_rust.NimbusClient(
            app_context, None, [], str(Path.cwd()), mock.Mock(), None, None
        )

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
                "user_clicked_tou_prompt_link": True,
                "user_clicked_tou_prompt_remind_me_later": True,
                "language": "en",
                "region": "US",
            }
        )

        targeting_helper = client.create_targeting_helper(
            additional_context=custom_targeting_attributes
        )

        try:
            test_expr = f"{expression} == true"
            targeting_helper.eval_jexl(test_expr)
        except Exception:
            try:
                targeting_helper.eval_jexl(expression)
            except Exception as e:
                raise Exception(
                    f"Rust JEXL evaluation failed for expression '{expression}': {e}"
                ) from e
