import json
import logging
from enum import Enum
from typing import Any

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .sdk import SDK

logger = logging.getLogger(__name__)


class RecipeType(Enum):
    ROLLOUT = "rollout"
    EXPERIMENT = "experiment"
    EMPTY = ""


class RemoteSettings:
    def __init__(self, url: str, sdk: SDK, retry: Retry | None = None):
        self.recipes: dict[str, list[Any]] = {"data": []}
        if url.endswith("/records"):
            raise ValueError("cirrus no longer supports remote settings records api")
        self.url: str = url
        self.sdk = sdk
        self.session = Session()
        if retry is not None:
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

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
        response = self.session.get(self.url)
        response.raise_for_status()
        response_json = response.json()
        data = response_json.get("changes")
        if data is not None:
            self.update_recipes({"data": data})
            logger.info(f"Fetched resources: {data}")
        else:
            logger.warning("No recipes found in the response")
