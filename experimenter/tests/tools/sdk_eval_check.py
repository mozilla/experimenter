import argparse
import json
from pathlib import Path

import nimbus_megazord.nimbus as nimbus


class MockMetricsHandler(nimbus.MetricsHandler):
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


def load_parser():
    parser = argparse.ArgumentParser(description="Load configurations")
    parser.add_argument("--targeting-string", type=str, action="store", nargs="?")
    return parser


def load_context():
    app_context_path = Path("app_context.json")
    if app_context_path.exists():
        with app_context_path.open() as file:
            data = json.loads(file.read())["app_context"]
            return nimbus.AppContext(
                app_id=data["app_id"],
                app_name=data["app_name"],
                channel=data["channel"],
                app_version=data["app_version"],
                app_build=data["app_build"],
                architecture=data["architecture"],
                device_manufacturer=data["device_manufacturer"],
                device_model=data["device_model"],
                locale=data["locale"],
                os=data["os"],
                os_version=data["os_version"],
                android_sdk_version=data["android_sdk_version"],
                debug_tag=data["debug_tag"],
                installation_date=data["installation_date"],
                custom_targeting_attributes=None,
            )
    else:
        print("Please provide an app context file. Exiting...")
        exit()


if __name__ == "__main__":
    args = load_parser().parse_args()

    context = load_context()

    client = nimbus.NimbusClient(
        context,
        None,
        [],
        str(Path.cwd()),
        None,
        MockMetricsHandler(),
        None,
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
            "is_apple_intelligence_available": True,
            "cannot_use_apple_intelligence": True,
            "install_referrer_response_utm_source": "test",
            "number_of_app_launches": 1,
            "is_large_device": True,
            "user_accepted_tou": True,
            "no_shortcuts_or_stories_opt_outs": True,
            "user_clicked_tou_prompt_link": True,
            "user_clicked_tou_prompt_remind_me_later": True,
        }
    )
    targeting_helper = client.create_targeting_helper(
        additional_context=custom_targeting_attributes
    )

    print(targeting_helper.eval_jexl(args.targeting_string))
