import os
import urllib

import kinto_http
import requests

ADMIN_USER = ADMIN_PASS = "admin"
REVIEW_USER = REVIEW_PASS = "review"
EXPERIMENTER_USER = os.environ["KINTO_USER"]
EXPERIMENTER_PASS = os.environ["KINTO_PASS"]


def create_user(user, passw):
    print(f">>>> Creating kinto user: {user}:{passw}")
    print(
        requests.put(
            urllib.parse.urljoin(os.environ["KINTO_HOST"], f"/accounts/{user}"),
            json={"data": {"password": passw}},
        ).content,
    )


create_user(ADMIN_USER, ADMIN_PASS)
create_user(REVIEW_USER, REVIEW_PASS)
create_user(EXPERIMENTER_USER, EXPERIMENTER_PASS)

client = kinto_http.Client(
    server_url=os.environ["KINTO_HOST"], auth=(ADMIN_USER, ADMIN_PASS)
)

print(f">>>> Creating kinto bucket: {os.environ['KINTO_BUCKET']}")
print(
    client.create_bucket(
        id=os.environ["KINTO_BUCKET"],
        permissions={"read": ["system.Everyone"]},
        if_not_exists=True,
    )
)


print(">>>> Creating kinto group: editors")
print(
    client.create_group(
        id=f"{os.environ['KINTO_COLLECTION']}-editors",
        bucket=os.environ["KINTO_BUCKET"],
        data={"members": [f"account:{os.environ['KINTO_USER']}"]},
        if_not_exists=True,
    )
)

print(">>>> Creating kinto group: reviewers")
print(
    client.create_group(
        id=f"{os.environ['KINTO_COLLECTION']}-reviewers",
        bucket=os.environ["KINTO_BUCKET"],
        data={"members": [f"account:{REVIEW_USER}"]},
        if_not_exists=True,
    )
)

print(f">>>> Creating kinto collection: {os.environ['KINTO_COLLECTION']}")
print(
    client.create_collection(
        id=os.environ["KINTO_COLLECTION"],
        bucket=os.environ["KINTO_BUCKET"],
        permissions={
            "read": ["system.Everyone"],
            "write": [
                (
                    f"/buckets/{os.environ['KINTO_BUCKET']}/groups/"
                    f"{os.environ['KINTO_COLLECTION']}-editors"
                ),
                (
                    f"/buckets/{os.environ['KINTO_BUCKET']}/groups/"
                    f"{os.environ['KINTO_COLLECTION']}-reviewers"
                ),
            ],
        },
        if_not_exists=True,
    )
)
