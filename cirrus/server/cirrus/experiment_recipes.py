import json
import logging
from enum import Enum
from typing import Any

import requests

from .sdk import SDK

logger = logging.getLogger(__name__)


class RecipeType(Enum):
    ROLLOUT = "rollout"
    EXPERIMENT = "experiment"
    EMPTY = ""


class RemoteSettings:
    def __init__(self, url: str, sdk: SDK):
        self.recipes: dict[str, list[Any]] = {"data": []}
        self.url: str = url
        self.sdk = sdk

    def get_recipes(self) -> dict[str, list[Any]]:
        return self.recipes

    def get_recipe_type(self, experiment_slug: str) -> str:
        experiment = {
            experiment["slug"]: experiment for experiment in self.recipes["data"]
        }.get(experiment_slug)
        if experiment is not None:
            return (
                RecipeType.ROLLOUT.value
                if experiment.get("isRollout", False)
                else RecipeType.EXPERIMENT.value
            )
        return RecipeType.EMPTY.value

    def update_recipes(self, new_recipes: dict[str, list[Any]]) -> None:
        self.recipes = new_recipes
        self.sdk.set_experiments(json.dumps(self.recipes))

    def fetch_recipes(self) -> None:
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            data = response.json().get("data")
            if data is not None:
                self.update_recipes({"data": data})
                logger.info(f"Fetched resources: {data}")
            else:
                logger.warning("No recipes found in the response")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch recipes: {e}")
            raise e
