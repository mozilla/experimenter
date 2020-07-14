import kinto_http
from django.conf import settings

KINTO_REVIEW_STATUS = "to-review"


def push_to_kinto(data):
    client = kinto_http.Client(
        server_url=settings.KINTO_HOST, auth=(settings.KINTO_USER, settings.KINTO_PASS),
    )
    client.create_record(
        data=data,
        collection=settings.KINTO_COLLECTION,
        bucket=settings.KINTO_BUCKET,
        if_not_exists=True,
    )
    client.patch_collection(
        id=settings.KINTO_COLLECTION,
        data={"status": KINTO_REVIEW_STATUS},
        bucket=settings.KINTO_BUCKET,
    )


def has_pending_review():
    client = kinto_http.Client(
        server_url=settings.KINTO_HOST, auth=(settings.KINTO_USER, settings.KINTO_PASS),
    )
    collection = client.get_collection(
        id=settings.KINTO_COLLECTION, bucket=settings.KINTO_BUCKET
    )
    return collection["data"]["status"] == KINTO_REVIEW_STATUS
