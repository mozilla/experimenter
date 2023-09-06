from unittest import mock

from experimenter.kinto.client import KINTO_REJECTED_STATUS, KINTO_REVIEW_STATUS


class MockKintoClientMixin:
    def setUp(self):
        super().setUp()

        mock_kinto_client_patcher = mock.patch(
            "experimenter.kinto.client.kinto_http.Client"
        )
        self.mock_kinto_client_creator = mock_kinto_client_patcher.start()
        self.mock_kinto_client = mock.Mock()
        self.mock_kinto_client_creator.return_value = self.mock_kinto_client
        self.addCleanup(mock_kinto_client_patcher.stop)

    def setup_kinto_pending_review(self):
        self.mock_kinto_client.get_collection.return_value = {
            "data": {"status": KINTO_REVIEW_STATUS}
        }

    def setup_kinto_no_pending_review(self):
        self.mock_kinto_client.get_collection.return_value = {
            "data": {"status": "anything"}
        }

    def setup_kinto_rejected_review(self):
        self.mock_kinto_client.get_collection.return_value = {
            "data": {
                "status": KINTO_REJECTED_STATUS,
                "last_reviewer_comment": "it's no good",
            }
        }

    def setup_kinto_get_main_records(self, slugs):
        self.mock_kinto_client.get_records.return_value = [
            {"id": slug, "last_modified": "0"} for slug in slugs
        ]
