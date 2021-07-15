import mock
from django.conf import settings
from django.test import TestCase

from experimenter.base import app_version


class TestBase(TestCase):
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
