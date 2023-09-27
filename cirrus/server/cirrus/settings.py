import json
import logging
from dataclasses import dataclass
from typing import Optional, Union, cast

from decouple import config  # type: ignore

remote_setting_refresh_rate_in_seconds: int = int(
    config("CIIRUS_REMOTE_SETTING_REFRESH_RATE_IN_SECONDS", default=10)  # type: ignore
)
remote_setting_url: str = cast(str, config("CIRRUS_REMOTE_SETTING_URL", default=""))

app_id: str = cast(str, config("CIRRUS_APP_ID", default=""))
app_name: str = cast(str, config("CIRRUS_APP_NAME", default=""))
channel: str = cast(str, config("CIRRUS_CHANNEL", default=""))

context: str = json.dumps(
    {
        "app_id": app_id,
        "app_name": app_name,
        "channel": channel,
    }
)
fml_path: str = cast(str, config("CIRRUS_FML_PATH", default=""))
pings_path: str = "./telemetry/pings.yaml"
metrics_path: str = "./telemetry/metrics.yaml"

cirrus_sentry_dsn: str = cast(str, config("CIRRUS_SENTRY_DSN", default=""))


@dataclass
class MetricsConfiguration:
    app_id: str = app_id
    build: Optional[str] = cast(
        Optional[str], config("CIRRUS_METRICS_BUILD", default=None)
    )
    channel: str = channel
    data_dir: str = cast(str, config("CIRRUS_METRICS_DATA_DIR", default="/var/glean"))
    log_level: Union[str, int] = cast(
        Union[str, int],
        logging.getLevelName(
            cast(str, config("CIRRUS_METRICS_LOG_LEVEL", default="WARNING"))
        ),
    )
    max_events_buffer: int = int(config("CIRRUS_METRICS_MAX_EVENTS_BUFFER", default=500))
    server_endpoint: Optional[str] = cast(
        Optional[str], config("CIRRUS_SERVER_ENDPOINT", default=None)
    )
    upload_enabled: bool = bool(config("CIRRUS_METRICS_UPLOAD_ENABLED", default=True))
    version: str = cast(str, config("CIRRUS_METRICS_VERSION", default="1.0"))


metrics_config = MetricsConfiguration()
