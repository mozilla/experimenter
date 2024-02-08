from unittest import mock

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.test import TestCase, override_settings
from inmemorystorage import InMemoryStorage

from experimenter.base import UploadsStorage, app_version, get_uploads_storage


class TestAppVersion(TestCase):
    def setUp(self):
        app_version.cache_clear()

    def test_app_version_file(self):
        expected_version = "8675309"
        version_json = f'{{"commit": "{expected_version}"}}'
        with self.settings(APP_VERSION=None), mock.patch(
            "experimenter.base.Path.open",
            mock.mock_open(read_data=version_json),
        ) as mf:
            version = app_version()
            self.assertEqual(version, expected_version)

            version_again = app_version()
            self.assertEqual(version_again, expected_version)

            mf.assert_called_once_with(settings.APP_VERSION_JSON_PATH)

    def test_app_version_env_over_file(self):
        expected_version = "thx1138"
        version_json = '{"commit": "INCORRECT"}'

        with self.settings(APP_VERSION=expected_version), mock.patch(
            "experimenter.base.Path.open",
            mock.mock_open(read_data=version_json),
        ) as mf:
            version = app_version()
            mf.assert_not_called()
            self.assertEqual(version, expected_version)

    def test_app_version_file_error(self):
        version_json = '{"commit": "INCORRECT"}'
        with self.settings(APP_VERSION=None), mock.patch(
            "experimenter.base.Path.open",
            mock.mock_open(read_data=version_json),
        ) as mf:
            mf.side_effect = OSError()
            version = app_version()
            mf.assert_called_once_with(settings.APP_VERSION_JSON_PATH)
            self.assertEqual(version, "")


class TestGetUploadsStorage(TestCase):
    @override_settings(UPLOADS_GS_BUCKET_NAME=None, UPLOADS_FILE_STORAGE=None)
    def test_get_uploads_storage_default(self):
        self.assertIsInstance(get_uploads_storage(), FileSystemStorage)

    @override_settings(
        UPLOADS_GS_BUCKET_NAME="bazquux",
        UPLOADS_FILE_STORAGE="inmemorystorage.InMemoryStorage",
    )
    def test_get_uploads_storage_custom(self):
        self.assertIsInstance(get_uploads_storage(), InMemoryStorage)

    @override_settings(
        UPLOADS_GS_BUCKET_NAME="bazquux",
        UPLOADS_FILE_STORAGE=None,
    )
    @mock.patch("experimenter.base.GoogleCloudStorage")
    def test_get_uploads_storage_gcp(self, MockGoogleCloudStorage):
        storage = get_uploads_storage()
        self.assertEqual(storage, MockGoogleCloudStorage.return_value)
        MockGoogleCloudStorage.assert_called_with(
            bucket_name="bazquux",
        )

    @mock.patch("experimenter.base.get_uploads_storage")
    def test_uploads_storage_class(self, mock_get_uploads_storage):
        storage = UploadsStorage()
        self.assertTrue(storage._wrapped, mock_get_uploads_storage.return_value)
