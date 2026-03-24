import json
from datetime import datetime
from sys import stdout
from typing import Any

from experimenter.glean.generated.server_events import GLEAN_EVENT_MOZLOG_TYPE


def get_request_ip(request) -> None | str:
    if xff := request.META.get("HTTP_X_FORWARDED_FOR"):
        # Only trust the last 3 values in XFF because they are added by the Google Cloud
        # Load Balancer and nginx, and use the least recent of those values.
        return xff.rsplit(",", 4)[-3:][0]
    return request.META.get("REMOTE_ADDR")


def emit_record(now: datetime, ping: dict[str, Any]):
    ping_envelope = {
        "Timestamp": now.isoformat(),
        "Logger": "glean",
        "Type": GLEAN_EVENT_MOZLOG_TYPE,
        "Fields": ping,
    }
    ping_envelope_serialized = f"{json.dumps(ping_envelope)}\n"
    stdout.write(ping_envelope_serialized)
