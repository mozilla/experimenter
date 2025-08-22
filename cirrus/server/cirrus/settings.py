import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, cast

from decouple import config  # type: ignore

remote_setting_refresh_rate_in_seconds: int = int(
    config("CIIRUS_REMOTE_SETTING_REFRESH_RATE_IN_SECONDS", default=10)  # type: ignore
)
remote_setting_refresh_retry_delay_in_seconds: int = int(
    config("CIIRUS_REMOTE_SETTING_REFRESH_RETRY_DELAY_IN_SECONDS", default=30)  # type: ignore
)
remote_setting_refresh_max_attempts: int = int(
    config("CIIRUS_REMOTE_SETTING_REFRESH_MAX_ATTEMPTS", default=3)  # type: ignore
)
remote_setting_url: str = cast(str, config("CIRRUS_REMOTE_SETTING_URL", default=""))
remote_setting_preview_url: str = cast(
    str, config("CIRRUS_REMOTE_SETTING_PREVIEW_URL", default="")
)

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
cirrus_sentry_traces_sample_rate: float = float(
    config("CIRRUS_SENTRY_TRACES_SAMPLE_RATE", default=0.25)  # type: ignore
)
cirrus_sentry_profiles_sample_rate: float = float(
    config("CIRRUS_SENTRY_PROFILES_SAMPLE_RATE", default=0.25)  # type: ignore
)

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
    data_dir: Path = Path("/var/glean") / str(os.getpid())
    log_level: Union[str, int] = logging.WARNING
    max_events_buffer: int = glean_max_events_buffer
    server_endpoint: Optional[str] = None
    upload_enabled: bool = True
    version: str = "1.0"


metrics_config = MetricsConfiguration()
