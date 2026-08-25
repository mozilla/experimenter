import logging
import os
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

# TEMP DO NOT MERGE: diagnostic instrumentation only.
logger = logging.getLogger(__name__)


def kinto_diag_log(message):
    worker = os.environ.get("PYTEST_XDIST_WORKER", "-")
    test = os.environ.get("PYTEST_CURRENT_TEST", "-")
    logger.info(f"KINTODIAG wall={time.time():.3f} worker={worker} test={test} {message}")


class KintoClient:
    RETRIES = 60

    def __init__(self, collection, server_url):
        self.collection = collection
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

    # TEMP DO NOT MERGE: diagnostic only. Compares the workspace bucket against
    # the signed main bucket so the slugs carried by a pending review can be
    # named. get_record_data() alone returns every workspace record, signed or
    # not, so it cannot distinguish the pending delta on its own.
    def _diag_pending_delta(self):
        workspace = {
            record.get("id"): (record.get("slug"), record.get("last_modified"))
            for record in self.get_record_data()
        }
        published = {
            record.get("id"): (record.get("slug"), record.get("last_modified"))
            for record in self.kinto_http_client.get_records(
                collection=self.collection, bucket=KINTO_BUCKET_MAIN
            )
        }
        added = sorted(
            slug for rid, (slug, _) in workspace.items() if rid not in published
        )
        changed = sorted(
            slug
            for rid, (slug, modified) in workspace.items()
            if rid in published and published[rid][1] != modified
        )
        removed = sorted(
            slug for rid, (slug, _) in published.items() if rid not in workspace
        )
        return added, changed, removed

    def _diag_pending_delta_str(self):
        try:
            added, changed, removed = self._diag_pending_delta()
        except Exception as e:
            return f"delta_error={e!r}"
        return f"added={added} changed={changed} removed={removed}"

    def approve(self, retries=RETRIES):
        started = time.monotonic()
        history = []
        kinto_diag_log(
            f"approve.enter collection={self.collection} retries={retries} "
            f"pid={os.getpid()}"
        )
        for attempt in range(1, retries + 1):
            collection_data = self._fetch_collection_data()
            status = collection_data.get("status")
            elapsed = time.monotonic() - started
            if status == KINTO_REVIEW_STATUS:
                delta = self._diag_pending_delta_str()
                requester = collection_data.get("last_review_request_by")
                kinto_diag_log(
                    f"approve.pending collection={self.collection} attempt={attempt} "
                    f"elapsed={elapsed:.1f}s {delta} "
                    f"last_review_request_by={requester} "
                    f"last_editor={collection_data.get('last_editor')}"
                )
                try:
                    self.kinto_http_client.patch_collection(
                        id=self.collection,
                        data={"status": KINTO_SIGN_STATUS},
                        bucket=KINTO_BUCKET_WORKSPACE,
                    )
                except kinto_http.exceptions.KintoException as e:
                    # This happens if there are multiple experiments that
                    # need to be approved.
                    history.append(f"{attempt}:{status}:exception")
                    kinto_diag_log(
                        f"approve.kinto_exception collection={self.collection} "
                        f"attempt={attempt} elapsed={elapsed:.1f}s {delta} error={e!r}"
                    )
                else:
                    kinto_diag_log(
                        f"approve.signed collection={self.collection} "
                        f"attempt={attempt} elapsed={elapsed:.1f}s {delta}"
                    )
                    return
            else:
                history.append(f"{attempt}:{status}")
                kinto_diag_log(
                    f"approve.waiting collection={self.collection} attempt={attempt} "
                    f"elapsed={elapsed:.1f}s status={status}"
                )
            time.sleep(2)
        kinto_diag_log(
            f"approve.exhausted collection={self.collection} retries={retries} "
            f"elapsed={time.monotonic() - started:.1f}s "
            f"{self._diag_pending_delta_str()} history={' '.join(history)}"
        )
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
            time.sleep(2)
        raise Exception("Unable to reject kinto review")

    def get_record_data(self):
        return self.kinto_http_client.get_records(
            collection=self.collection, bucket=KINTO_BUCKET_WORKSPACE
        )
