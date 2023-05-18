import json
from typing import Dict, List

from cirrus_sdk import CirrusClient  # type: ignore

from .settings import context

client = CirrusClient(context)


class SDK:
    client = CirrusClient(context)

    def compute_enrollments(
        self, targeting_context: Dict[str, str]
    ) -> List[Dict[str, str]]:
        res = client.handle_enrollment(json.dumps(targeting_context))  # type: ignore
        return json.loads(res)

    def set_experiments(self, recipes: str):
        client.set_experiments(recipes)  # type: ignore


sdk = SDK()
