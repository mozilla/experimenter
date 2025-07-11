from dataclasses import dataclass
from typing import Any

import requests
import sentry_sdk
from django.conf import settings


class CirrusFeatures:
    def __init__(self, data: dict[str, dict[str, Any]]):
        self._data = data

    @property
    def is_example_feature_enabled(self) -> bool:
        return self._data.get("example-feature", {}).get("enabled")

    @property
    def example_feature_emoji(self) -> str:
        return self._data.get("example-feature", {}).get("emoji")


@dataclass
class CirrusData:
    enrollments: list[dict[str, str]]
    features: CirrusFeatures


class CirrusMiddleware:
    """
    A middleware that provides experiment enrollment information via Nimbus.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.cirrus_url = settings.CIRRUS_URL

    def __call__(self, request):
        request.cirrus = None
        if hasattr(request, "user") and request.user.id and self.cirrus_url:
            params = {}
            if (nimbus_preview := request.GET.get("nimbus_preview")) is not None:
                params["nimbus_preview"] = nimbus_preview
            try:
                cirrus_response = requests.post(
                    self.cirrus_url,
                    # NOTE(relud): context must not be empty
                    json={"client_id": str(request.user.id), "context": {"": ""}},
                    params=params,
                )
                cirrus_response.raise_for_status()
                response_json = cirrus_response.json()
                request.cirrus = CirrusData(
                    enrollments=response_json["Enrollments"],
                    features=CirrusFeatures(response_json["Features"]),
                )
            except (KeyError, requests.exceptions.RequestException) as e:
                sentry_sdk.capture_exception(e)
        return self.get_response(request)
