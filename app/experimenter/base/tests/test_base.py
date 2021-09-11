import mock
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.test import TestCase, override_settings

from experimenter.base import app_version, get_uploads_storage


class TestAppVersion(TestCase):
    def setUp(self):
        app_version.cache_clear()

    def test_app_version_file(self):
        expected_version = "8675309"
        version_json = f'{{"commit": "{expected_version}"}}'
        with self.settings(APP_VERSION=None):
            with mock.patch(
                "experimenter.base.open",
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

        with self.settings(APP_VERSION=expected_version):
            with mock.patch(
                "experimenter.base.open",
                mock.mock_open(read_data=version_json),
            ) as mf:
                version = app_version()
                mf.assert_not_called()
                self.assertEqual(version, expected_version)

    def test_app_version_file_error(self):
        version_json = '{"commit": "INCORRECT"}'
        with self.settings(APP_VERSION=None):
            with mock.patch(
                "builtins.open",
                mock.mock_open(read_data=version_json),
            ) as mf:
                mf.side_effect = IOError()
                version = app_version()
                mf.assert_called_once_with(settings.APP_VERSION_JSON_PATH)
                self.assertEqual(version, "")


class TestGetUploadsStorage(TestCase):
    def setUp(self):
        get_uploads_storage.cache_clear()

    @override_settings(UPLOADS_GS_CREDENTIALS=None)
    def test_get_uploads_storage_file(self):
        storage = get_uploads_storage()
        self.assertIsInstance(storage, FileSystemStorage)

    @mock.patch("experimenter.base.service_account")
    @mock.patch("experimenter.base.GoogleCloudStorage")
    def test_get_uploads_storage_gcp(self, MockGoogleCloudStorage, mock_service_account):
        expected_bucket_name = "bazquux"
        expected_credentials = "/app/uploads-credentials.json"

        with self.settings(
            UPLOADS_GS_BUCKET_NAME=expected_bucket_name,
            UPLOADS_GS_CREDENTIALS=expected_credentials,
        ):
            storage = get_uploads_storage()
            self.assertEqual(storage, MockGoogleCloudStorage.return_value)

            from_service_account_file = (
                mock_service_account.Credentials.from_service_account_file
            )
            from_service_account_file.assert_called_with(
                expected_credentials,
            )
            mock_credentials = from_service_account_file.return_value
            MockGoogleCloudStorage.assert_called_with(
                credentials=mock_credentials,
                project_id=mock_credentials.project_id,
                bucket_name=expected_bucket_name,
            )
