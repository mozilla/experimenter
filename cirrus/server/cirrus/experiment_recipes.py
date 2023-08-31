import json
import logging
from enum import Enum
from typing import Any

import requests

from .sdk import SDK
from .settings import remote_setting_url

logger = logging.getLogger(__name__)


class RecipeType(Enum):
    ROLLOUT = "rollout"
    EXPERIMENT = "experiment"
    EMPTY = ""


class RemoteSettings:
    def __init__(self, sdk: SDK):
        self.recipes: dict[str, list[Any]] = {"data": []}
        self.url: str = remote_setting_url
        self.sdk = sdk

    def get_recipes(self) -> dict[str, list[Any]]:
        return self.recipes

    def get_recipe_type(self, experiment_slug: str) -> str:
        for experiment in self.get_recipes()["data"]:
            if experiment["slug"] == experiment_slug:
                if experiment.get("isRollout", False):
                    return RecipeType.ROLLOUT.value
                else:
                    return RecipeType.EXPERIMENT.value

        return RecipeType.EMPTY.value

    def update_recipes(self, new_recipes: dict[str, list[Any]]) -> None:
        self.recipes = new_recipes
        self.sdk.set_experiments(json.dumps(self.recipes))

    def fetch_recipes(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # raises an HTTPError for bad status codes
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch recipes: {e}")
            raise e
        data = response.json().get("data")
        if data is not None:
            self.update_recipes({"data": data})
            logger.info(f"Fetched resources: {data}")
        else:
            logger.warning("No recipes found in the response")
