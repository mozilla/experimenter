import json
import logging
from typing import Any, Dict, List

import requests

from .sdk import sdk
from .settings import remote_setting_url

logger = logging.getLogger(__name__)


class RemoteSettings:
    recipes: Dict[str, List[Any]] = {"data": []}
    url: str = remote_setting_url

    def get_recipes(self) -> Dict[str, List[Any]]:
        return self.recipes

    def update_recipes(self, new_recipes: Dict[str, List[Any]]) -> None:
        self.recipes = new_recipes
        sdk.set_experiments(json.dumps(self.recipes))

    def fetch_recipes(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # raises an HTTPError for bad status codes
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch recipes: {e}")
            raise e
        if data := response.json().get("data", {"data": []}):
            self.update_recipes({"data": data})
            logger.info("Fetched resources")
        else:
            logger.warning("No recipes found in the response")


remote_setting = RemoteSettings()
