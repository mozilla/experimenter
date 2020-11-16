from django.conf import settings
from django.test import TestCase

from experimenter.kinto.client import KintoClient
from experimenter.kinto.tests.mixins import MockKintoClientMixin


class TestKintoClient(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.collection = "test-collection"
        self.client = KintoClient(self.collection)

    def test_push_to_kinto_sends_data_updates_collection(self):
        self.client.push_to_kinto({"test": "data"})

        self.mock_kinto_client_creator.assert_called_with(
            server_url=settings.KINTO_HOST,
            auth=(settings.KINTO_USER, settings.KINTO_PASS),
        )

        self.mock_kinto_client.create_record.assert_called_with(
            data={"test": "data"},
            collection=self.collection,
            bucket=settings.KINTO_BUCKET,
            if_not_exists=True,
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": "to-review"},
            bucket=settings.KINTO_BUCKET,
        )

    def test_delete_rejected_record_removes_record_patches_collection(self):
        self.client.delete_rejected_record("test_id")

        self.mock_kinto_client_creator.assert_called_with(
            server_url=settings.KINTO_HOST,
            auth=(settings.KINTO_USER, settings.KINTO_PASS),
        )

        self.mock_kinto_client.delete_record.assert_called_with(
            id="test_id",
            bucket=settings.KINTO_BUCKET,
            collection=self.collection,
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": "to-review"},
            bucket=settings.KINTO_BUCKET,
        )

    def test_returns_true_for_pending_review(self):
        self.setup_kinto_pending_review()
        self.assertTrue(self.client.has_pending_review())

    def test_returns_false_for_no_pending_review(self):
        self.setup_kinto_no_pending_review()
        self.assertFalse(self.client.has_pending_review())

    def test_returns_records(self):
        slug = "test-slug"
        self.setup_kinto_get_main_records([slug])
        self.assertEqual(self.client.get_main_records(), [{"id": slug}])

    def test_returns_no_records(self):
        self.setup_kinto_get_main_records([])
        self.assertEqual(self.client.get_main_records(), [])

    def test_returns_nothing_when_not_rejects(self):
        self.setup_kinto_no_pending_review()
        self.assertIsNone(self.client.get_rejected_collection_data())

    def test_returns_rejected_data(self):
        self.setup_kinto_rejected_review()
        self.assertTrue(self.client.get_rejected_collection_data())

    def test_returns_rejected_record(self):
        self.mock_kinto_client.get_records.side_effect = [
            [{"id": "bug-12345-rapid-test-release-55"}],
            [
                {"id": "bug-12345-rapid-test-release-55"},
                {"id": "bug-9999-rapid-test-release-55"},
            ],
        ]
        self.assertEqual(
            self.client.get_rejected_record(), "bug-9999-rapid-test-release-55"
        )
