import kinto_http
from django.conf import settings

KINTO_REVIEW_STATUS = "to-review"
KINTO_REJECTED_STATUS = "work-in-progress"


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


def get_rejected_collection_data():
    client = kinto_http.Client(
        server_url=settings.KINTO_HOST, auth=(settings.KINTO_USER, settings.KINTO_PASS),
    )
    collection = client.get_collection(
        id=settings.KINTO_COLLECTION, bucket=settings.KINTO_BUCKET
    )

    if collection["data"]["status"] == KINTO_REJECTED_STATUS:
        return collection["data"]


def get_rejected_record():
    client = kinto_http.Client(
        server_url=settings.KINTO_HOST, auth=(settings.KINTO_USER, settings.KINTO_PASS),
    )

    main_records = client.get_records(
        bucket=settings.KINTO_BUCKET_MAIN, collection=settings.KINTO_COLLECTION
    )

    workspace_records = client.get_records(
        bucket=settings.KINTO_BUCKET, collection=settings.KINTO_COLLECTION
    )

    main_record_ids = [record["id"] for record in main_records]

    workspace_record_ids = [record["id"] for record in workspace_records]

    return list(set(workspace_record_ids) - set(main_record_ids))


def delete_rejected_record(record_id):
    client = kinto_http.Client(
        server_url=settings.KINTO_HOST, auth=(settings.KINTO_USER, settings.KINTO_PASS),
    )
    client.delete_record(
        id=record_id, bucket=settings.KINTO_BUCKET, collection=settings.KINTO_COLLECTION
    )


def get_main_records():
    client = kinto_http.Client(
        server_url=settings.KINTO_HOST, auth=(settings.KINTO_USER, settings.KINTO_PASS),
    )
    return client.get_records(
        bucket=settings.KINTO_BUCKET_MAIN, collection=settings.KINTO_COLLECTION
    )
