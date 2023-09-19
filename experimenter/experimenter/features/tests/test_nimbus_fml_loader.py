from unittest import mock

from django.test import TestCase

from experimenter.features.manifests.nimbus_fml_loader import NimbusFmlLoader


class TestNimbusFmlLoader(TestCase):
    def test_intiate_new_fml_client_no_error(self):
        application = "fenix"
        channel = "production"

        with mock.patch(
            "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.create",
        ) as create:
            loader = NimbusFmlLoader(application, channel)

            self.assertEqual(loader.application, application)
            self.assertEqual(loader.channel, channel)
            create.assert_called_once()

    def test_intiate_invalid_fml_client_errors(self):
        application = "rats"
        channel = "production"

        with self.assertLogs(level="ERROR") as log:
            with mock.patch(
                "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.create",
            ) as create:
                loader = NimbusFmlLoader(application, channel)
                self.assertIn(
                    "Failed to find fml path for application: rats", log.output[0]
                )

            self.assertEqual(loader.application, application)
            self.assertEqual(loader.channel, channel)
            create.assert_not_called()

    def test_create(self):
        application = "fenix"
        channel = "production"

        loader = NimbusFmlLoader(application, channel)
        response = loader.create("my/favorite/path", "ziggy")
        # Todo: Connect FML https://mozilla-hub.atlassian.net/browse/EXP-3791
        self.assertEqual(response, "success")
