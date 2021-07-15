import json
from functools import cache

from django.conf import settings


@cache
def app_version():
    app_version = settings.APP_VERSION

    if app_version is None:
        try:
            with open(settings.APP_VERSION_JSON_PATH) as version_json_file:
                version_json = json.load(version_json_file)
                app_version = version_json["commit"]
        except IOError:
            # EXP-1384: Preserve default blank version if version.json unavailable
            app_version = ""

    return app_version
