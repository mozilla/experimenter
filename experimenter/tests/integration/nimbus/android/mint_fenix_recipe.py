#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INTEGRATION_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(INTEGRATION_ROOT))

from nimbus.utils import helpers

FENIX_APP = "fenix"
FEATURE_SLUG = "messaging"


def wait_for_recipe(base_url, slug, timeout=60):
    url = urljoin(base_url, f"/api/v6/experiments/{slug}/")
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, verify=False, timeout=5)
            if resp.status_code == 200:
                recipe = resp.json()
                if recipe.get("slug") == slug and recipe.get("bucketConfig"):
                    return recipe
                last_error = f"recipe missing bucketConfig: {recipe.get('bucketConfig')!r}"
            else:
                last_error = f"HTTP {resp.status_code}"
        except (requests.RequestException, ValueError) as exc:
            last_error = str(exc)
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for recipe at {url} ({last_error})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    feature_id = helpers.get_feature_id_as_string(FEATURE_SLUG, FENIX_APP)
    if not feature_id:
        raise RuntimeError(
            f"Could not resolve feature id for '{FEATURE_SLUG}' in app '{FENIX_APP}'"
        )

    helpers.create_experiment(
        args.slug,
        FENIX_APP,
        data={
            "feature_config_ids": [int(feature_id)],
            "reference_branch": {
                "name": "control",
                "description": "control branch",
            },
            "population_percent": "100",
            "total_enrolled_clients": "1000000",
            "channel": "release",
        },
        targeting="no_targeting",
    )

    print(f"Transitioning {args.slug} draft → preview to allocate bucket range")
    helpers._post_form(f"/nimbus/{args.slug}/draft-to-preview/")

    base_url = helpers._get_nginx_url()
    recipe = wait_for_recipe(base_url, args.slug)
    Path(args.output).write_text(json.dumps(recipe, indent=2))
    print(f"Wrote recipe: {args.output}")


if __name__ == "__main__":
    main()
