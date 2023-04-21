from django.conf import settings
from django.test import TestCase
from parameterized import parameterized

from experimenter.kinto.client import (
    REMOTE_SETTINGS_REVIEW_STATUS,
    REMOTE_SETTINGS_ROLLBACK_STATUS,
    REMOTE_SETTINGS_SIGN_STATUS,
    RemoteSettingsClient,
)
from experimenter.kinto.tests.mixins import MockRemoteSettingsClientMixin


class TestRemoteSettingsClient(MockRemoteSettingsClientMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.collection = "test-collection"
        self.client = RemoteSettingsClient(self.collection)

    @parameterized.expand(
        [
            [False, REMOTE_SETTINGS_SIGN_STATUS],
            [True, REMOTE_SETTINGS_REVIEW_STATUS],
        ]
    )
    def test_create_record_creates_record_patches_collection(self, review, status):
        client = RemoteSettingsClient(self.collection, review=review)
        client.create_record({"test": "data"})

        self.mock_rs_client_creator.assert_called_with(
            server_url=settings.REMOTE_SETTINGS_HOST,
            auth=(settings.REMOTE_SETTINGS_USER, settings.REMOTE_SETTINGS_PASS),
        )

        self.mock_rs_client.create_record.assert_called_with(
            data={"test": "data"},
            collection=self.collection,
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
            if_not_exists=True,
        )

        self.mock_rs_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": status},
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
        )

    @parameterized.expand(
        [
            [False, REMOTE_SETTINGS_SIGN_STATUS],
            [True, REMOTE_SETTINGS_REVIEW_STATUS],
        ]
    )
    def test_update_record_updates_record_patches_collection(self, review, status):
        client = RemoteSettingsClient(self.collection, review=review)

        data = {"id": "my-record", "field": "value"}
        client.update_record(data)

        self.mock_rs_client.update_record.assert_called_with(
            data=data,
            collection=self.collection,
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
            if_match='"0"',
        )

        self.mock_rs_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": status},
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
        )

    @parameterized.expand(
        [
            [False, REMOTE_SETTINGS_SIGN_STATUS],
            [True, REMOTE_SETTINGS_REVIEW_STATUS],
        ]
    )
    def test_delete_record_deletes_record_patches_collection(self, review, status):
        client = RemoteSettingsClient(self.collection, review=review)

        record_id = "abc-123"
        client.delete_record(record_id)

        self.mock_rs_client_creator.assert_called_with(
            server_url=settings.REMOTE_SETTINGS_HOST,
            auth=(settings.REMOTE_SETTINGS_USER, settings.REMOTE_SETTINGS_PASS),
        )

        self.mock_rs_client.delete_record.assert_called_with(
            id=record_id,
            collection=self.collection,
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
        )

        self.mock_rs_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": status},
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
        )

    def test_rollback_changes_patches_collection(self):
        self.client.rollback_changes()

        self.mock_rs_client_creator.assert_called_with(
            server_url=settings.REMOTE_SETTINGS_HOST,
            auth=(settings.REMOTE_SETTINGS_USER, settings.REMOTE_SETTINGS_PASS),
        )

        self.mock_rs_client.patch_collection.assert_called_with(
            id=self.collection,
            data={"status": REMOTE_SETTINGS_ROLLBACK_STATUS},
            bucket=settings.REMOTE_SETTINGS_SIGN_STATUS,
        )

    def test_returns_true_for_pending_review(self):
        self.setup_remote_settings_pending_review()
        self.assertTrue(self.client.has_pending_review())

    def test_returns_false_for_no_pending_review(self):
        self.setup_remote_settings_no_pending_review()
        self.assertFalse(self.client.has_pending_review())

    def test_returns_records(self):
        slug = "test-slug"
        self.setup_remote_settings_get_main_records([slug])
        self.assertEqual(
            self.client.get_main_records(), {slug: {"id": slug, "last_modified": "0"}}
        )

    def test_returns_no_records(self):
        self.setup_remote_settings_get_main_records([])
        self.assertEqual(self.client.get_main_records(), {})

    def test_returns_nothing_when_not_rejects(self):
        self.setup_remote_settings_no_pending_review()
        self.assertIsNone(self.client.get_rejected_collection_data())

    def test_returns_rejected_data(self):
        self.setup_remote_settings_rejected_review()
        self.assertTrue(self.client.get_rejected_collection_data())
