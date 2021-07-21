from django.conf import settings
from django.test import TestCase
from parameterized import parameterized

from experimenter.kinto.client import (
    KINTO_REVIEW_STATUS,
    KINTO_ROLLBACK_STATUS,
    KINTO_SIGN_STATUS,
    KintoClient,
)
from experimenter.kinto.tests.mixins import MockKintoClientMixin


class TestKintoClient(MockKintoClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.collection = "test-collection"
        self.client = KintoClient(self.collection)

    @parameterized.expand(
        [
            [False, KINTO_SIGN_STATUS],
            [True, KINTO_REVIEW_STATUS],
        ]
    )
    def test_create_record_creates_record_patches_collection(self, review, status):
        client = KintoClient(self.collection, review=review)
        client.create_record({"test": "data"})

        self.mock_kinto_client_creator.assert_called_with(
            server_url=settings.KINTO_HOST,
            auth=(settings.KINTO_USER, settings.KINTO_PASS),
        )

        self.mock_kinto_client.create_record.assert_called_with(
            data={"test": "data"},
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": status},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    @parameterized.expand(
        [
            [False, KINTO_SIGN_STATUS],
            [True, KINTO_REVIEW_STATUS],
        ]
    )
    def test_update_record_updates_record_patches_collection(self, review, status):
        client = KintoClient(self.collection, review=review)

        data = {"id": "my-record", "field": "value"}
        client.update_record(data)

        self.mock_kinto_client.update_record.assert_called_with(
            data=data,
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_match='"0"',
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": status},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    @parameterized.expand(
        [
            [False, KINTO_SIGN_STATUS],
            [True, KINTO_REVIEW_STATUS],
        ]
    )
    def test_delete_record_deletes_record_patches_collection(self, review, status):
        client = KintoClient(self.collection, review=review)

        record_id = "abc-123"
        client.delete_record(record_id)

        self.mock_kinto_client_creator.assert_called_with(
            server_url=settings.KINTO_HOST,
            auth=(settings.KINTO_USER, settings.KINTO_PASS),
        )

        self.mock_kinto_client.delete_record.assert_called_with(
            id=record_id,
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": status},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def test_rollback_changes_patches_collection(self):
        self.client.rollback_changes()

        self.mock_kinto_client_creator.assert_called_with(
            server_url=settings.KINTO_HOST,
            auth=(settings.KINTO_USER, settings.KINTO_PASS),
        )

        self.mock_kinto_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": KINTO_ROLLBACK_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
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
        self.assertEqual(
            self.client.get_main_records(), {slug: {"id": slug, "last_modified": "0"}}
        )

    def test_returns_no_records(self):
        self.setup_kinto_get_main_records([])
        self.assertEqual(self.client.get_main_records(), {})

    def test_returns_nothing_when_not_rejects(self):
        self.setup_kinto_no_pending_review()
        self.assertIsNone(self.client.get_rejected_collection_data())

    def test_returns_rejected_data(self):
        self.setup_kinto_rejected_review()
        self.assertTrue(self.client.get_rejected_collection_data())
