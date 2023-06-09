import json
from typing import cast

from decouple import config  # type: ignore

remote_setting_refresh_rate_in_seconds: int = int(
    config("REMOTE_SETTING_REFRESH_RATE_IN_SECONDS", default=10)  # type: ignore
)
remote_setting_url: str = cast(str, config("REMOTE_SETTING_URL", default=""))

app_id: str = cast(str, config("APP_ID", default=""))
app_name: str = cast(str, config("APP_NAME", default=""))
channel: str = cast(str, config("CHANNEL", default=""))

context: str = json.dumps(
    {
        "app_id": app_id,
        "app_name": app_name,
        "channel": channel,
    }
)
fml_path: str = cast(str, config("CIRRUS_FML_PATH", default=""))
