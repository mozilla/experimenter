import json
from functools import cache

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from google.oauth2 import service_account
from storages.backends.gcloud import GoogleCloudStorage


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


@cache
def get_uploads_storage():
    if settings.UPLOADS_GS_CREDENTIALS:
        credentials = service_account.Credentials.from_service_account_file(
            settings.UPLOADS_GS_CREDENTIALS
        )
        return GoogleCloudStorage(
            credentials=credentials,
            project_id=credentials.project_id,
            bucket_name=settings.UPLOADS_GS_BUCKET_NAME,
        )

    return FileSystemStorage()
