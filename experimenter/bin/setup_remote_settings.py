import os
import time
import urllib

import kinto_http
import requests

ADMIN_USER = ADMIN_PASS = "admin"
REVIEW_USER = REVIEW_PASS = "review"
EXPERIMENTER_USER = os.getenv("REMOTE_SETTINGS_USER", os.getenv("KINTO_USER"))
EXPERIMENTER_PASS = os.getenv("REMOTE_SETTINGS_PASS", os.getenv("KINTO_PASS"))
REMOTE_SETTINGS_HOST = os.getenv("REMOTE_SETTINGS_HOST", os.getenv("KINTO_HOST"))
REMOTE_SETTINGS_BUCKET_WORKSPACE = "main-workspace"
REMOTE_SETTINGS_BUCKET_MAIN = "main"
REMOTE_SETTINGS_COLLECTION_NIMBUS_DESKTOP = "nimbus-desktop-experiments"
REMOTE_SETTINGS_COLLECTION_NIMBUS_MOBILE = "nimbus-mobile-experiments"
REMOTE_SETTINGS_COLLECTION_NIMBUS_PREVIEW = "nimbus-preview"


def create_user(user, passw):
    print(f">>>> Creating Remote Settings user: {user}:{passw}")
    print(
        requests.put(
            urllib.parse.urljoin(REMOTE_SETTINGS_HOST, f"/accounts/{user}"),
            json={"data": {"password": passw}},
        ).content,
    )


def setup():
    create_user(ADMIN_USER, ADMIN_PASS)
    create_user(REVIEW_USER, REVIEW_PASS)
    create_user(EXPERIMENTER_USER, EXPERIMENTER_PASS)

    client = kinto_http.Client(server_url=REMOTE_SETTINGS_HOST, auth=(ADMIN_USER, ADMIN_PASS))

    print(f">>>> Creating Remote Settings bucket: {REMOTE_SETTINGS_BUCKET_WORKSPACE}")
    print(
        client.create_bucket(
            id=REMOTE_SETTINGS_BUCKET_WORKSPACE,
            permissions={"read": ["system.Everyone"]},
            if_not_exists=True,
        )
    )

    for collection in [
        REMOTE_SETTINGS_COLLECTION_NIMBUS_DESKTOP,
        REMOTE_SETTINGS_COLLECTION_NIMBUS_MOBILE,
        REMOTE_SETTINGS_COLLECTION_NIMBUS_PREVIEW,
    ]:
        print(">>>> Creating Remote Settings group: editors")
        print(
            client.create_group(
                id=f"{collection}-editors",
                bucket=REMOTE_SETTINGS_BUCKET_WORKSPACE,
                data={"members": [f"account:{EXPERIMENTER_USER}"]},
                if_not_exists=True,
            )
        )

        print(">>>> Creating Remote Settings group: reviewers")
        print(
            client.create_group(
                id=f"{collection}-reviewers",
                bucket=REMOTE_SETTINGS_BUCKET_WORKSPACE,
                data={"members": [f"account:{REVIEW_USER}"]},
                if_not_exists=True,
            )
        )

        print(f">>>> Creating Remote Settings collection: {collection}")
        print(
            client.create_collection(
                id=collection,
                bucket=REMOTE_SETTINGS_BUCKET_WORKSPACE,
                permissions={
                    "read": ["system.Everyone"],
                    "write": [
                        (
                            f"/buckets/{REMOTE_SETTINGS_BUCKET_WORKSPACE}/groups/"
                            f"{collection}-editors"
                        ),
                        (
                            f"/buckets/{REMOTE_SETTINGS_BUCKET_WORKSPACE}/groups/"
                            f"{collection}-reviewers"
                        ),
                    ],
                },
                if_not_exists=True,
            )
        )


while True:
    try:
        setup()
        exit()
    except Exception:
        time.sleep(1)
