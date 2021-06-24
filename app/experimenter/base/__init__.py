import json
import os

from django.conf import settings

APP_VERSION = None


def app_version():
    global APP_VERSION

    if APP_VERSION is None:
        if settings.APP_VERSION:
            APP_VERSION = settings.APP_VERSION
        else:
            try:
                version_json_path = os.path.join(settings.BASE_DIR, "version.json")
                with open(version_json_path) as version_json_file:
                    version_json = json.load(version_json_file)
                    APP_VERSION = version_json["commit"]
            except IOError:
                # EXP-1384: Preserve default blank version if version.json unavailable
                APP_VERSION = ""

    return APP_VERSION
