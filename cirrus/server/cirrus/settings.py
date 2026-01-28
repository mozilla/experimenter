import json
from typing import cast

from decouple import config  # type: ignore

remote_setting_refresh_rate_in_seconds: int = int(
    config("CIRRUS_REMOTE_SETTING_REFRESH_RATE_IN_SECONDS", default=10)  # type: ignore
)
remote_setting_refresh_jitter_in_seconds: int = int(
    config("CIRRUS_REMOTE_SETTING_REFRESH_JITTER_IN_SECONDS", default=1)  # type: ignore
)
remote_setting_retry_backoff_factor_in_seconds: int = int(
    config("CIRRUS_REMOTE_SETTING_RETRY_BACKOFF_FACTOR_IN_SECONDS", default=1)  # type: ignore
)
remote_setting_retry_total: int = int(
    config("CIRRUS_REMOTE_SETTING_RETRY_TOTAL", default=5)  # type: ignore
)
remote_setting_require_fetch_before_start: bool = (
    config("CIRRUS_REMOTE_SETTING_REQUIRE_FETCH_BEFORE_START", default="").lower()  # type: ignore
    in ("true", "yes", "1")
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
