from typing import cast
from decouple import config  # type: ignore

remote_setting_refresh_rate_in_seconds: int = int(
    config("REMOTE_SETTING_REFRESH_RATE_IN_SECONDS", default=10)  # type: ignore
)
remote_setting_url: str = cast(str, config("REMOTE_SETTING_URL", default=""))
