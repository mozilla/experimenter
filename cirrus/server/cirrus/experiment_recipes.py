import json
import logging
from typing import Any, Dict, List

import requests

from .sdk import SDK
from .settings import remote_setting_url

logger = logging.getLogger(__name__)
from enum import Enum


class RecipeType(Enum):
    ROLLOUT = "rollout"
    EXPERIMENT = "experiment"
    EMPTY = ""


class RemoteSettings:
    def __init__(self, sdk: SDK):
        self.recipes: Dict[str, List[Any]] = {"data": []}
        self.url: str = remote_setting_url
        self.sdk = sdk

    def get_recipes(self) -> Dict[str, List[Any]]:
        return self.recipes

    def get_recipe_type(self, experiment_slug: str) -> str:
        recipes_data = self.get_recipes()["data"]
        if not recipes_data:
            return RecipeType.EMPTY.value

        for experiment in recipes_data:
            if experiment["slug"] == experiment_slug:
                is_rollout = experiment.get("isRollout", False)
                if is_rollout:
                    return RecipeType.ROLLOUT.value
                else:
                    return RecipeType.EXPERIMENT.value

        return RecipeType.EMPTY.value

    def update_recipes(self, new_recipes: Dict[str, List[Any]]) -> None:
        self.recipes = new_recipes
        self.sdk.set_experiments(json.dumps(self.recipes))

    def fetch_recipes(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # raises an HTTPError for bad status codes
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch recipes: {e}")
            raise e

        data = response.json().get("data", [])
        if data:
            self.update_recipes({"data": data})
            logger.info("Fetched resources")
        else:
            logger.warning("No recipes found in the response")
