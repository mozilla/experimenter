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
instance_name: str = cast(
    str, config("CIRRUS_INSTANCE_NAME", default="instance name not defined")
)
env_name = cast(str, config("CIRRUS_ENV_NAME", default="production"))
glean_max_events_buffer: int = int(
    config("CIRRUS_GLEAN_MAX_EVENTS_BUFFER", default=10)  # type: ignore
)


@dataclass
class MetricsConfiguration:
    app_id: str = app_id
    build: Optional[str] = None
    channel: str = channel
    data_dir: str = "/var/glean"
    log_level: Union[str, int] = logging.getLevelName("WARNING")
    max_events_buffer: int = glean_max_events_buffer
    server_endpoint: Optional[str] = None
    upload_enabled: bool = True
    version: str = "1.0"


metrics_config = MetricsConfiguration()
