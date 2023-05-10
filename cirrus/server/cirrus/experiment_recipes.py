import logging
from typing import Any, Dict, List, cast

import requests
from decouple import config  # type: ignore

logger = logging.getLogger(__name__)


class RemoteSettings:
    recipes: List[Dict[str, Any]] = []
    url: str = cast(str, config("REMOTE_SETTING_URL", default=""))

    def get_recipes(self) -> List[Dict[str, Any]]:
        return self.recipes

    def update_recipes(self, new_recipes: List[Dict[str, Any]]) -> None:
        self.recipes = new_recipes

    def fetch_recipes(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                data = response.json().get("data", [])
                if data:
                    self.update_recipes(data)
                    logger.info("Fetched resources")
                else:
                    logger.warning("No recipes found in the response")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch recipes: {e}")
            raise e
