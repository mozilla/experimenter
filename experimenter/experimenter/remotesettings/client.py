import kinto_http
from django.conf import settings

REMOTE_SETTINGS_REVIEW_STATUS = "to-review"
REMOTE_SETTINGS_REJECTED_STATUS = "work-in-progress"
REMOTE_SETTINGS_ROLLBACK_STATUS = "to-rollback"
REMOTE_SETTINGS_SIGN_STATUS = "to-sign"


class RemoteSettingsClient:
    def __init__(self, collection, review=True):
        self.collection = collection
        self.kinto_http_client = kinto_http.Client(
            server_url=settings.REMOTE_SETTINGS_HOST,
            auth=(settings.REMOTE_SETTINGS_USER, settings.REMOTE_SETTINGS_PASS),
        )
        self.review = review
        self.collection_data = None

    def _fetch_collection_data(self):
        self.collection_data = (
            self.collection_data
            or self.kinto_http_client.get_collection(
                id=self.collection, bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE
            )["data"]
        )

    def _patch_collection(self):
        if self.review:
            self.kinto_http_client.patch_collection(
                id=self.collection,
                data={"status": REMOTE_SETTINGS_REVIEW_STATUS},
                bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
            )
        else:
            self.kinto_http_client.patch_collection(
                id=self.collection,
                data={"status": REMOTE_SETTINGS_SIGN_STATUS},
                bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
            )

    def create_record(self, data):
        self.kinto_http_client.create_record(
            data=data,
            collection=self.collection,
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
            if_not_exists=True,
        )
        self._patch_collection()

    def update_record(self, data):
        self.kinto_http_client.update_record(
            data=data,
            collection=self.collection,
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
            if_match='"0"',
        )
        self._patch_collection()

    def delete_record(self, record_id):
        self.kinto_http_client.delete_record(
            id=record_id,
            collection=self.collection,
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
        )
        self._patch_collection()

    def has_pending_review(self):
        self._fetch_collection_data()
        if self.collection_data:
            return self.collection_data["status"] == REMOTE_SETTINGS_REVIEW_STATUS

    def has_rejection(self):
        self._fetch_collection_data()
        if self.collection_data:
            return self.collection_data["status"] == REMOTE_SETTINGS_REJECTED_STATUS

    def get_rejected_collection_data(self):
        self._fetch_collection_data()
        if (
            self.collection_data
            and self.collection_data["status"] == REMOTE_SETTINGS_REJECTED_STATUS
        ):
            return self.collection_data

    def rollback_changes(self):
        self.kinto_http_client.patch_collection(
            id=self.collection,
            data={"status": REMOTE_SETTINGS_ROLLBACK_STATUS},
            bucket=settings.REMOTE_SETTINGS_BUCKET_WORKSPACE,
        )

    def get_main_records(self):
        return {
            r["id"]: r
            for r in self.kinto_http_client.get_records(
                bucket=settings.REMOTE_SETTINGS_BUCKET_MAIN, collection=self.collection
            )
        }
