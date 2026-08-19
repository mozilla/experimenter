#!/usr/bin/env python3
"""Validate targeting SQL expressions against BigQuery's query planner.

Reads a JSON file produced by `manage.py export_targeting_sql` and POSTs each
query to Mozilla's dryrun Cloud Function, which runs BigQuery's query planner
without executing or scanning any data.

Auth: reads GOOGLE_GHA_ID_TOKEN from the environment (set by the
google-github-actions/auth step in GitHub Actions). Falls back to Application
Default Credentials for local runs.

Exit code: 0 if all queries pass, 1 if any fail.
"""

import json
import os
import random
import sys
from urllib.request import Request, urlopen

DRY_RUN_URL = "https://us-central1-moz-fx-data-shared-prod.cloudfunctions.net/dryrun"
BILLING_PROJECTS = [
    "moz-fx-data-backfill-10",
    "moz-fx-data-backfill-11",
    "moz-fx-data-backfill-12",
]


def get_id_token():
    token = os.environ.get("GOOGLE_GHA_ID_TOKEN")
    if token:
        return token

    import google.auth
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from google.oauth2.id_token import fetch_id_token

    auth_req = GoogleAuthRequest()
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(auth_req)
    if hasattr(creds, "id_token"):
        return creds.id_token
    return fetch_id_token(auth_req, DRY_RUN_URL)


def dry_run(sql, id_token):
    billing_project = random.choice(BILLING_PROJECTS)
    payload = json.dumps(
        {"dataset": "mozanalysis", "query": sql, "billing_project": billing_project}
    ).encode("utf-8")
    req = Request(
        DRY_RUN_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {id_token}",
        },
        data=payload,
        method="POST",
    )
    r = urlopen(req)
    return json.load(r)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <targeting_sql.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        entries = json.load(f)

    if not entries:
        print("No entries to validate.")
        sys.exit(0)

    print(f"Validating {len(entries)} targeting SQL expressions...")
    id_token = get_id_token()

    failed = []
    for entry in entries:
        slug = entry["slug"]
        query = entry["query"]
        try:
            response = dry_run(query, id_token)
            if response.get("valid"):
                print(f"  ✓ {slug}")
            else:
                errors = response.get("errors", [])
                msg = errors[0].get("message") if errors else "unknown error"
                print(f"  ✗ {slug}: {msg}")
                failed.append(slug)
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
            failed.append(slug)

    print(f"\n{len(entries) - len(failed)}/{len(entries)} passed.")
    if failed:
        print(f"Failed: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
