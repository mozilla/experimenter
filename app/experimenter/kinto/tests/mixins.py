import mock


class MockKintoClientMixin(object):
    def setUp(self):
        super().setUp()

        mock_kinto_client_patcher = mock.patch(
            "experimenter.kinto.client.kinto_http.Client"
        )
        self.mock_kinto_client_creator = mock_kinto_client_patcher.start()
        self.mock_kinto_client = mock.Mock()
        self.mock_kinto_client_creator.return_value = self.mock_kinto_client
        self.addCleanup(mock_kinto_client_patcher.stop)
