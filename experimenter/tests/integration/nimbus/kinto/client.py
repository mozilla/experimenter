import time

import kinto_http

KINTO_HOST = "http://kinto:8888/v1"
KINTO_USER = "review"
KINTO_PASS = "review"
KINTO_COLLECTION_DESKTOP = "nimbus-desktop-experiments"
KINTO_COLLECTION_MOBILE = "nimbus-mobile-experiments"
KINTO_COLLECTION_WEB = "nimbus-web-experiments"
KINTO_BUCKET_WORKSPACE = "main-workspace"
KINTO_REVIEW_STATUS = "to-review"
KINTO_REJECTED_STATUS = "work-in-progress"
KINTO_SIGN_STATUS = "to-sign"


class KintoClient:
    RETRIES = 60

    def __init__(self, collection):
        self.collection = collection
        self.kinto_http_client = kinto_http.Client(
            server_url=KINTO_HOST,
            auth=(KINTO_USER, KINTO_PASS),
        )

    def _fetch_collection_data(self):
        return self.kinto_http_client.get_collection(
            id=self.collection, bucket=KINTO_BUCKET_WORKSPACE
        )["data"]

    def _has_pending_review(self):
        return self._fetch_collection_data()["status"] == KINTO_REVIEW_STATUS

    def approve(self):
        for _ in range(self.RETRIES):
            if self._has_pending_review():
                try:
                    self.kinto_http_client.patch_collection(
                        id=self.collection,
                        data={"status": KINTO_SIGN_STATUS},
                        bucket=KINTO_BUCKET_WORKSPACE,
                    )
                except kinto_http.exceptions.KintoException:
                    # This happens if there are multiple experiments that
                    # need to be approved.
                    pass
                else:
                    return
            time.sleep(1)
        raise Exception("Unable to approve kinto review")

    def reject(self):
        for _ in range(self.RETRIES):
            if self._has_pending_review():
                self.kinto_http_client.patch_collection(
                    id=self.collection,
                    data={
                        "status": KINTO_REJECTED_STATUS,
                        "last_reviewer_comment": "Rejected",
                    },
                    bucket=KINTO_BUCKET_WORKSPACE,
                )
                return
            time.sleep(1)
        raise Exception("Unable to reject kinto review")
