import time

import kinto_http

KINTO_HOST = "http://kinto:8888/v1"
KINTO_USER = "review"
KINTO_PASS = "review"
KINTO_COLLECTION_DESKTOP = "nimbus-desktop-experiments"
KINTO_COLLECTION_MOBILE = "nimbus-mobile-experiments"
KINTO_COLLECTION_WEB = "nimbus-web-experiments"
KINTO_COLLECTION_PREVIEW = "nimbus-preview"
KINTO_BUCKET_WORKSPACE = "main-workspace"
KINTO_BUCKET_MAIN = "main"
KINTO_REVIEW_STATUS = "to-review"
KINTO_REJECTED_STATUS = "work-in-progress"
KINTO_SIGN_STATUS = "to-sign"


class KintoClient:
    RETRIES = 60

    def __init__(self, collection, server_url, slug=None):
        self.collection = collection
        self.slug = slug
        self.kinto_http_client = kinto_http.Client(
            server_url=server_url,
            auth=(KINTO_USER, KINTO_PASS),
        )

    def _fetch_collection_data(self):
        return self.kinto_http_client.get_collection(
            id=self.collection, bucket=KINTO_BUCKET_WORKSPACE
        )["data"]

    def _has_pending_review(self):
        return self._fetch_collection_data()["status"] == KINTO_REVIEW_STATUS

    def _diffing_record_ids(self):
        workspace_records = {
            record["id"]: {
                key: value for key, value in record.items() if key != "last_modified"
            }
            for record in self.get_record_data()
        }
        main_records = {
            record["id"]: {
                key: value for key, value in record.items() if key != "last_modified"
            }
            for record in self.get_main_record_data()
        }
        return sorted(
            set(workspace_records) ^ set(main_records)
            | {
                record_id
                for record_id in workspace_records.keys() & main_records.keys()
                if workspace_records[record_id] != main_records[record_id]
            }
        )

    def _sign(self):
        try:
            self.kinto_http_client.patch_collection(
                id=self.collection,
                data={"status": KINTO_SIGN_STATUS},
                bucket=KINTO_BUCKET_WORKSPACE,
            )
        except kinto_http.exceptions.KintoException:
            # This happens if there are multiple experiments that
            # need to be approved.
            return False
        return True

    def approve(self, retries=RETRIES):
        for _ in range(retries):
            collection_data = self._fetch_collection_data()
            if collection_data["status"] == KINTO_REVIEW_STATUS:
                diffing_ids = self._diffing_record_ids()
                is_own_review = self.slug is None or self.slug in diffing_ids
                if is_own_review:
                    if self._sign():
                        return
                else:
                    self._sign()
            time.sleep(2)
        raise Exception("Unable to approve kinto review")

    def reject(self):
        for _ in range(self.RETRIES):
            if self._has_pending_review():
                diffing_ids = self._diffing_record_ids()
                if self.slug is None or self.slug in diffing_ids:
                    self.kinto_http_client.patch_collection(
                        id=self.collection,
                        data={
                            "status": KINTO_REJECTED_STATUS,
                            "last_reviewer_comment": "Rejected",
                        },
                        bucket=KINTO_BUCKET_WORKSPACE,
                    )
                    return
                self._sign()
            time.sleep(2)
        raise Exception("Unable to reject kinto review")

    def get_record_data(self):
        return self.kinto_http_client.get_records(
            collection=self.collection, bucket=KINTO_BUCKET_WORKSPACE
        )

    def get_main_record_data(self):
        return self.kinto_http_client.get_records(
            collection=self.collection, bucket=KINTO_BUCKET_MAIN
        )
