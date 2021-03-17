import kinto_http
from django.conf import settings

KINTO_REVIEW_STATUS = "to-review"
KINTO_REJECTED_STATUS = "work-in-progress"
KINTO_ROLLBACK_STATUS = "to-rollback"
KINTO_SIGN_STATUS = "to-sign"


class KintoClient:
    def __init__(self, collection, review=True):
        self.collection = collection
        self.kinto_http_client = kinto_http.Client(
            server_url=settings.KINTO_HOST,
            auth=(settings.KINTO_USER, settings.KINTO_PASS),
        )
        self.review = review
        self.collection_data = None

    def _fetch_collection_data(self):
        self.collection_data = (
            self.collection_data
            or self.kinto_http_client.get_collection(
                id=self.collection, bucket=settings.KINTO_BUCKET_WORKSPACE
            )["data"]
        )

    def _patch_collection(self):
        if self.review:
            self.kinto_http_client.patch_collection(
                id=self.collection,
                data={"status": KINTO_REVIEW_STATUS},
                bucket=settings.KINTO_BUCKET_WORKSPACE,
            )
        else:
            self.kinto_http_client.patch_collection(
                id=self.collection,
                data={"status": KINTO_SIGN_STATUS},
                bucket=settings.KINTO_BUCKET_WORKSPACE,
            )

    def create_record(self, data):
        self.kinto_http_client.create_record(
            data=data,
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )
        self._patch_collection()

    def update_record(self, data):
        self.kinto_http_client.update_record(
            data=data,
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_match='"0"',
        )
        self._patch_collection()

    def delete_record(self, id):
        self.kinto_http_client.delete_record(
            id=id,
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )
        self._patch_collection()

    def has_pending_review(self):
        self._fetch_collection_data()
        return self.collection_data["status"] == KINTO_REVIEW_STATUS

    def has_rejection(self):
        self._fetch_collection_data()
        return self.collection_data["status"] == KINTO_REJECTED_STATUS

    def get_rejected_collection_data(self):
        self._fetch_collection_data()
        if self.collection_data["status"] == KINTO_REJECTED_STATUS:
            return self.collection_data

    def get_rejected_record(self):
        main_records = self.kinto_http_client.get_records(
            bucket=settings.KINTO_BUCKET_MAIN, collection=self.collection
        )

        workspace_records = self.kinto_http_client.get_records(
            bucket=settings.KINTO_BUCKET_WORKSPACE, collection=self.collection
        )

        main_record_ids = [record["id"] for record in main_records]

        workspace_record_ids = [record["id"] for record in workspace_records]
        return list(set(workspace_record_ids) - set(main_record_ids))[0]

    def rollback_changes(self):
        self.kinto_http_client.patch_collection(
            id=self.collection,
            data={"status": KINTO_ROLLBACK_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def get_main_records(self):
        return self.kinto_http_client.get_records(
            bucket=settings.KINTO_BUCKET_MAIN, collection=self.collection
        )
