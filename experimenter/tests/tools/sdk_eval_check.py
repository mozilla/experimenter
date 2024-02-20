import argparse
import json
from pathlib import Path

import nimbus_rust as nimbus


def load_parser():
    parser = argparse.ArgumentParser(description="Load configurations")
    parser.add_argument("--targeting-string", type=str, action="store", nargs="?")
    return parser


def load_context():
    app_context_path = Path("app_context.json")
    if app_context_path.exists():
        with app_context_path.open() as file:
            data = json.loads(file.read())["app_context"]
            return (
                nimbus.AppContext(
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
                    home_directory=data["home_directory"],
                    custom_targeting_attributes=data["custom_targeting_attributes"],
                ),
                data["additional_targeting"],
            )
    else:
        print("Please provide an app context file. Exiting...")
        exit()


if __name__ == "__main__":
    args = load_parser().parse_args()

    context, additional_targeting = load_context()

    randomization_units = nimbus.AvailableRandomizationUnits(None, 0)

    client = nimbus.NimbusClient(context, Path.cwd(), None, randomization_units)

    targeting_helper = client.create_targeting_helper(json.dumps(additional_targeting))

    print(targeting_helper.eval_jexl(args.targeting_string))
