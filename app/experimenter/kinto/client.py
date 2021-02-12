import kinto_http
from django.conf import settings

KINTO_REVIEW_STATUS = "to-review"
KINTO_REJECTED_STATUS = "work-in-progress"
KINTO_ROLLBACK_STATUS = "to-rollback"


class KintoClient:
    def __init__(self, collection):
        self.collection = collection
        self.kinto_http_client = kinto_http.Client(
            server_url=settings.KINTO_HOST,
            auth=(settings.KINTO_USER, settings.KINTO_PASS),
        )

    def push_to_kinto(self, data):
        self.kinto_http_client.create_record(
            data=data,
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_not_exists=True,
        )
        self.kinto_http_client.patch_collection(
            id=self.collection,
            data={"status": KINTO_REVIEW_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def update_record(self, data):
        self.kinto_http_client.update_record(
            data=data,
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
            if_match='"0"',
        )
        self.kinto_http_client.patch_collection(
            id=self.collection,
            data={"status": KINTO_REVIEW_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )

    def has_pending_review(self):
        collection = self.kinto_http_client.get_collection(
            id=self.collection, bucket=settings.KINTO_BUCKET_WORKSPACE
        )
        return collection["data"]["status"] == KINTO_REVIEW_STATUS

    def get_rejected_collection_data(self):
        collection = self.kinto_http_client.get_collection(
            id=self.collection, bucket=settings.KINTO_BUCKET_WORKSPACE
        )

        if collection["data"]["status"] == KINTO_REJECTED_STATUS:
            return collection["data"]

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

    def delete_from_kinto(self, id):
        self.kinto_http_client.delete_record(
            id=id,
            collection=self.collection,
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )
        self.kinto_http_client.patch_collection(
            id=self.collection,
            data={"status": KINTO_REVIEW_STATUS},
            bucket=settings.KINTO_BUCKET_WORKSPACE,
        )
