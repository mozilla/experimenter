import mock

from experimenter.kinto.client import REMOTE_SETTINGS_REJECTED_STATUS, REMOTE_SETTINGS_REVIEW_STATUS


class MockRemoteSettingsClientMixin(object):
    def setUp(self):
        super().setUp()

        mock_rs_client_patcher = mock.patch(
            "experimenter.kinto.client.kinto_http.Client"
        )
        self.mock_rs_client_creator = mock_rs_client_patcher.start()
        self.mock_rs_client = mock.Mock()
        self.mock_rs_client_creator.return_value = self.mock_rs_client
        self.addCleanup(mock_rs_client_patcher.stop)

    def setup_remote_settings_pending_review(self):
        self.mock_rs_client.get_collection.return_value = {
            "data": {"status": REMOTE_SETTINGS_REVIEW_STATUS}
        }

    def setup_remote_settings_no_pending_review(self):
        self.mock_rs_client.get_collection.return_value = {
            "data": {"status": "anything"}
        }

    def setup_remote_settings_rejected_review(self):
        self.mock_rs_client.get_collection.return_value = {
            "data": {
                "status": REMOTE_SETTINGS_REJECTED_STATUS,
                "last_reviewer_comment": "it's no good",
            }
        }

    def setup_remote_settings_get_main_records(self, slugs):
        self.mock_rs_client.get_records.return_value = [
            {"id": slug, "last_modified": "0"} for slug in slugs
        ]
