from typing import Any, Dict, List


class RemoteSettings:
    recipes: List[Dict[str, Any]] = []

    @classmethod
    def get_recipes(cls) -> List[Dict[str, Any]]:
        return cls.recipes

    @classmethod
    def update_recipes(cls, new_recipes: List[Dict[str, Any]]) -> None:
        cls.recipes = new_recipes
