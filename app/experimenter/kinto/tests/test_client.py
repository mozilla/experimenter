from django.conf import settings
from django.test import TestCase

from experimenter.kinto import client
from experimenter.kinto.tests.mixins import MockKintoClientMixin


class TestPushToKinto(MockKintoClientMixin, TestCase):
    def test_push_to_kinto_sends_data_updates_collection(self):
        client.push_to_kinto({"test": "data"})

        self.mock_kinto_client_creator.assert_called_with(
            server_url=settings.KINTO_HOST,
            auth=(settings.KINTO_USER, settings.KINTO_PASS),
        )

        self.mock_kinto_client.create_record.assert_called_with(
            data={"test": "data"},
            collection=settings.KINTO_COLLECTION,
            bucket=settings.KINTO_BUCKET,
            if_not_exists=True,
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=settings.KINTO_COLLECTION,
            data={"status": "to-review"},
            bucket=settings.KINTO_BUCKET,
        )


class TestHasPendingReview(MockKintoClientMixin, TestCase):
    def test_returns_true_for_pending_review(self):
        self.setup_kinto_pending_review()
        self.assertTrue(client.has_pending_review())

    def test_returns_false_for_no_pending_review(self):
        self.setup_kinto_no_pending_review()
        self.assertFalse(client.has_pending_review())


class TestGetMainRecords(MockKintoClientMixin, TestCase):
    def test_returns_records(self):
        self.setup_kinto_get_main_records()
        self.assertEqual(len(client.get_main_records()), 1)

    def test_returns_no_records(self):
        self.setup_kinto_no_main_records()
        self.assertEqual(client.get_main_records(), [])


class TestGetRejectedCollectionData(MockKintoClientMixin, TestCase):
    def test_returns_nothing_when_not_rejects(self):
        self.setup_kinto_no_pending_review()
        self.assertIsNone(client.get_rejected_collection_data())

    def test_returns_rejected_data(self):
        self.setup_kinto_rejected_review()
        self.assertTrue(client.get_rejected_collection_data())


class TestGetRejectedRecords(MockKintoClientMixin, TestCase):
    def test_returns_rejected_record(self):
        self.mock_kinto_client.get_records.side_effect = [
            [{"id": "bug-12345-rapid-test-release-55"}],
            [
                {"id": "bug-12345-rapid-test-release-55"},
                {"id": "bug-9999-rapid-test-release-55"},
            ],
        ]
        self.assertEqual(client.get_rejected_record(), ["bug-9999-rapid-test-release-55"])
