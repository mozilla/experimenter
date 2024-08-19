from unittest import mock

from django.test import TestCase

from experimenter.base import app_version


class TestAppVersion(TestCase):
    def setUp(self):
        app_version.cache_clear()

    @mock.patch("experimenter.base.settings.APP_VERSION_JSON_PATH")
    def test_app_version_file(self, mock_app_version_json_path):
        expected_version = "8675309"
        version_json = f'{{"commit": "{expected_version}"}}'
        mock_app_version_json_path.open = mock.mock_open(read_data=version_json)

        version = app_version()
        self.assertEqual(version, expected_version)

        version_again = app_version()
        self.assertEqual(version_again, expected_version)

    @mock.patch("experimenter.base.settings.APP_VERSION_JSON_PATH")
    def test_app_version_env_over_file(self, mock_app_version_json_path):
        expected_version = "thx1138"
        version_json = '{"commit": "INCORRECT"}'
        mock_app_version_json_path.open = mock.mock_open(read_data=version_json)

        with self.settings(APP_VERSION=expected_version):
            version = app_version()
            mock_app_version_json_path.assert_not_called()
            self.assertEqual(version, expected_version)

    @mock.patch("experimenter.base.settings.APP_VERSION_JSON_PATH")
    def test_app_version_file_error(self, mock_app_version_json_path):
        mock_app_version_json_path.open.side_effect = OSError()

        version = app_version()
        mock_app_version_json_path.open.assert_called_once()
        self.assertEqual(version, "")
