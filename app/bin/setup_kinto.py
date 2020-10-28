import os
import urllib

import kinto_http
import requests

ADMIN_USER = ADMIN_PASS = "admin"
REVIEW_USER = REVIEW_PASS = "review"
EXPERIMENTER_USER = os.environ["KINTO_USER"]
EXPERIMENTER_PASS = os.environ["KINTO_PASS"]
KINTO_HOST = os.environ["KINTO_HOST"]
KINTO_BUCKET = os.environ["KINTO_BUCKET"]
KINTO_COLLECTION_LEGACY = (os.environ["KINTO_COLLECTION"],)
KINTO_COLLECTION_NIMBUS = os.environ["KINTO_COLLECTION_NIMBUS"]


def create_user(user, passw):
    print(f">>>> Creating kinto user: {user}:{passw}")
    print(
        requests.put(
            urllib.parse.urljoin(KINTO_HOST, f"/accounts/{user}"),
            json={"data": {"password": passw}},
        ).content,
    )


create_user(ADMIN_USER, ADMIN_PASS)
create_user(REVIEW_USER, REVIEW_PASS)
create_user(EXPERIMENTER_USER, EXPERIMENTER_PASS)

client = kinto_http.Client(server_url=KINTO_HOST, auth=(ADMIN_USER, ADMIN_PASS))

print(f">>>> Creating kinto bucket: {KINTO_BUCKET}")
print(
    client.create_bucket(
        id=KINTO_BUCKET,
        permissions={"read": ["system.Everyone"]},
        if_not_exists=True,
    )
)


for collection in [KINTO_COLLECTION_LEGACY, KINTO_COLLECTION_NIMBUS]:
    print(">>>> Creating kinto group: editors")
    print(
        client.create_group(
            id=f"{collection}-editors",
            bucket=KINTO_BUCKET,
            data={"members": [f"account:{EXPERIMENTER_USER}"]},
            if_not_exists=True,
        )
    )

    print(">>>> Creating kinto group: reviewers")
    print(
        client.create_group(
            id=f"{collection}-reviewers",
            bucket=KINTO_BUCKET,
            data={"members": [f"account:{REVIEW_USER}"]},
            if_not_exists=True,
        )
    )

    print(f">>>> Creating kinto collection: {collection}")
    print(
        client.create_collection(
            id=collection,
            bucket=KINTO_BUCKET,
            permissions={
                "read": ["system.Everyone"],
                "write": [
                    (f"/buckets/{KINTO_BUCKET}/groups/" f"{collection}-editors"),
                    (f"/buckets/{KINTO_BUCKET}/groups/" f"{collection}-reviewers"),
                ],
            },
            if_not_exists=True,
        )
    )
