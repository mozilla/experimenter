import json
import os
from pathlib import Path

import pytest


@pytest.fixture(name="ios_channel")
def fixture_ios_channel():
    return os.environ.get("IOS_CHANNEL", "developer")


@pytest.fixture(name="ios_app_path")
def fixture_ios_app_path():
    return os.environ["IOS_APP_PATH"]


@pytest.fixture(name="ios_recipe_path")
def fixture_ios_recipe_path():
    return Path(os.environ["IOS_RECIPE_PATH"])


@pytest.fixture(name="ios_recipe")
def fixture_ios_recipe(ios_recipe_path):
    return json.loads(ios_recipe_path.read_text())
