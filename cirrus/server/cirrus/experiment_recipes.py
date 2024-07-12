import json
import logging
from enum import Enum
from typing import Any, Callable

import requests

from .sdk import SDK
from .settings import remote_setting_preview_url, remote_setting_url

logger = logging.getLogger(__name__)


class RecipeType(Enum):
    ROLLOUT = "rollout"
    EXPERIMENT = "experiment"
    EMPTY = ""


class RemoteSettings:
    def __init__(self, sdk_live: SDK, sdk_preview: SDK):
        self.live_recipes: dict[str, list[Any]] = {"data": []}
        self.preview_recipes: dict[str, list[Any]] = {"data": []}
        self.url: str = remote_setting_url
        self.preview_url: str = remote_setting_preview_url
        self.sdk_live = sdk_live
        self.sdk_preview = sdk_preview

    def get_recipes(self) -> dict[str, list[Any]]:
        return self.live_recipes

    def get_preview_recipes(self) -> dict[str, list[Any]]:
        return self.preview_recipes

    def get_live_recipe_type(self, experiment_slug: str) -> str:
        return self._get_live_recipe_type(self.get_recipes(), experiment_slug)

    def get_preview_recipe_type(self, experiment_slug: str) -> str:
        return self._get_live_recipe_type(self.get_preview_recipes(), experiment_slug)

    def _get_live_recipe_type(
        self, recipes: dict[str, list[Any]], experiment_slug: str
    ) -> str:
        for experiment in recipes["data"]:
            if experiment["slug"] == experiment_slug:
                return (
                    RecipeType.ROLLOUT.value
                    if experiment.get("isRollout", False)
                    else RecipeType.EXPERIMENT.value
                )
        return RecipeType.EMPTY.value

    def fetch_recipes(self) -> None:
        self._fetch_and_update(self.url, self.update_live_recipes)
        self._fetch_and_update(self.preview_url, self.update_preview_recipes)

    def _fetch_and_update(
        self, url: str, update_method: Callable[[dict[str, Any]], None]
    ) -> None:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json().get("data")
            if data is not None:
                update_method({"data": data})
                logger.info(f"Fetched resources: {data}")
            else:
                logger.warning("No recipes found in the response")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch recipes: {e}")
            raise e

    def update_live_recipes(self, new_recipes: dict[str, list[Any]]) -> None:
        self.live_recipes = new_recipes
        self.sdk_live.set_experiments(json.dumps(self.live_recipes))

    def update_preview_recipes(self, new_recipes: dict[str, list[Any]]) -> None:
        self.preview_recipes = new_recipes
        self.sdk_preview.set_experiments(json.dumps(self.preview_recipes))
