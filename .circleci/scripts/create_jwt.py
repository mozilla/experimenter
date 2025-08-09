#!/usr/bin/env python3
import sys
import os
import time

import jwt
import requests


app_id = os.environ["GH_APP_ID"]
installation_id = os.environ["GH_INSTALLATION_ID"]
private_key = os.environ["GH_APP_PRIVATE_KEY"].replace("\\n", "\n")

now = int(time.time())
payload = {
    "iat": now,
    "exp": now + 540,
    "iss": app_id
}
jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

# Get installation token
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Accept": "application/vnd.github+json"
}
response = requests.post(
    f"https://api.github.com/app/installations/{installation_id}/access_tokens",
    headers=headers
)
token = response.json()["token"]
print(token)
