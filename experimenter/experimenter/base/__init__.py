import json
from functools import cache
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage, get_storage_class
from django.utils.functional import LazyObject
from storages.backends.gcloud import GoogleCloudStorage


@cache
def app_version():
    app_version = settings.APP_VERSION

    if app_version is None:
        try:
            with Path.open(settings.APP_VERSION_JSON_PATH) as version_json_file:
                version_json = json.load(version_json_file)
                app_version = version_json["commit"]
        except OSError:
            # EXP-1384: Preserve default blank version if version.json unavailable
            app_version = ""

    return app_version


def get_uploads_storage():
    if settings.UPLOADS_FILE_STORAGE:
        cls = get_storage_class(settings.UPLOADS_FILE_STORAGE)
        return cls()

    if settings.UPLOADS_GS_BUCKET_NAME:
        return GoogleCloudStorage(
            bucket_name=settings.UPLOADS_GS_BUCKET_NAME,
        )

    return FileSystemStorage()


# Borrowing Django's DefaultStorage lazy object approach
# https://github.com/django/django/blob/ddae36700d1c07cbca15a6821bd99d480294c137/django/core/files/storage.py#L271-L273
class UploadsStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_uploads_storage()
