import time

import kinto_http

REMOTE_SETTINGS_HOST = "http://remote-settings:8888/v1"
REMOTE_SETTINGS_USER = "review"
REMOTE_SETTINGS_PASS = "review"
REMOTE_SETTINGS_COLLECTION_DESKTOP = "nimbus-desktop-experiments"
REMOTE_SETTINGS_COLLECTION_MOBILE = "nimbus-mobile-experiments"
REMOTE_SETTINGS_BUCKET_WORKSPACE = "main-workspace"
REMOTE_SETTINGS_REVIEW_STATUS = "to-review"
REMOTE_SETTINGS_REJECTED_STATUS = "work-in-progress"
REMOTE_SETTINGS_SIGN_STATUS = "to-sign"


class RemoteSettingsClient:
    def __init__(self, collection):
        self.collection = collection
        self.kinto_http_client = kinto_http.Client(
            server_url=REMOTE_SETTINGS_HOST,
            auth=(REMOTE_SETTINGS_USER, REMOTE_SETTINGS_PASS),
        )

    def _fetch_collection_data(self):
        return self.kinto_http_client.get_collection(
            id=self.collection, bucket=REMOTE_SETTINGS_BUCKET_WORKSPACE
        )["data"]

    def _has_pending_review(self):
        return self._fetch_collection_data()["status"] == REMOTE_SETTINGS_REVIEW_STATUS

    def approve(self):
        for _ in range(60):
            if self._has_pending_review():
                try:
                    self.kinto_http_client.patch_collection(
                        id=self.collection,
                        data={"status": REMOTE_SETTINGS_SIGN_STATUS},
                        bucket=REMOTE_SETTINGS_BUCKET_WORKSPACE,
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
        for _ in range(20):
            if self._has_pending_review():
                self.kinto_http_client.patch_collection(
                    id=self.collection,
                    data={
                        "status": REMOTE_SETTINGS_REJECTED_STATUS,
                        "last_reviewer_comment": "Rejected",
                    },
                    bucket=REMOTE_SETTINGS_BUCKET_WORKSPACE,
                )
                return
            time.sleep(1)
        raise Exception("Unable to reject kinto review")
