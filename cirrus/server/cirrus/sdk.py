import json
import logging
from typing import Any, Dict

from cirrus_sdk import CirrusClient, NimbusError  # type: ignore

logger = logging.getLogger(__name__)


class SDK:
    def __init__(self, context: str):
        self.client = CirrusClient(context)  # does not match struct- throw an exception

    def compute_enrollments(self, targeting_context: Dict[str, str]) -> Dict[str, Any]:
        try:
            res = self.client.handle_enrollment(  # type: ignore
                json.dumps(targeting_context)
            )
            return json.loads(res)
        except (NimbusError, Exception) as e:
            logger.error(f"An error occurred during compute_enrollments: {e}")
            return {}

    def set_experiments(self, recipes: str):
        try:
            self.client.set_experiments(recipes)  # type: ignore
        except NimbusError as e:
            logger.error(f"An error occurred during set_experiments: {e}")
