from unittest import mock


class MockFmlErrorMixin:
    def setUp(self):
        super().setUp()

        mock_fml_errors_patch = mock.patch(
            "experimenter.features.manifests.nimbus_fml_loader.NimbusFmlLoader.get_fml_errors",
        )
        self.mock_fml_errors = mock_fml_errors_patch.start()
        self.addCleanup(mock_fml_errors_patch.stop)

    def setup_fml_no_errors(self):
        self.mock_fml_errors.return_value = []

    def setup_get_fml_errors(self, fml_errors):
        self.mock_fml_errors.return_value = fml_errors
