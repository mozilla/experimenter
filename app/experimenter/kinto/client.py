import kinto_http
from django.conf import settings


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
        data={"status": "to-review"},
        bucket=settings.KINTO_BUCKET,
    )
