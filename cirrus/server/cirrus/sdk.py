import json
import logging
from typing import Any, Dict, List

from cirrus_sdk import CirrusClient, NimbusError  # type: ignore

logger = logging.getLogger(__name__)


class SDK:
    def __init__(self, context: str, coenrolling_feature_ids: List[str]):
        self.client = CirrusClient(context, coenrolling_feature_ids)

    def compute_enrollments(self, targeting_context: Dict[str, str]) -> Dict[str, Any]:
        try:
            res = self.client.handle_enrollment(json.dumps(targeting_context))
            return json.loads(res)
        except (NimbusError, Exception) as e:  # type: ignore
            logger.error(f"An error occurred during compute_enrollments: {e}")
            return {}

    def set_experiments(self, recipes: str):
        try:
            self.client.set_experiments(recipes)
        except NimbusError as e:  # type: ignore
            logger.error(f"An error occurred during set_experiments: {e}")
