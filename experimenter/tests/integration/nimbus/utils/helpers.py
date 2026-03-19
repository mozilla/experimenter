import json
import os
import time
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin

import requests

from nimbus.models.base_dataclass import (
    BaseExperimentApplications,
)

LOAD_DATA_RETRIES = 60
LOAD_DATA_RETRY_DELAY = 1.0
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
TARGETING_CONFIGS_PATH = FIXTURES_DIR / "targeting_configs.json"
FEATURE_CONFIGS_PATH = FIXTURES_DIR / "feature_configs.json"

NO_FEATURE_SLUGS = {
    BaseExperimentApplications.FIREFOX_DESKTOP.value: "no-feature-firefox-desktop",
    BaseExperimentApplications.FIREFOX_FENIX.value: "no-feature-fenix",
    BaseExperimentApplications.FIREFOX_IOS.value: "no-feature-ios",
}

_session = None


def _get_nginx_url():
    return os.getenv("INTEGRATION_TEST_NGINX_URL", "https://nginx")


def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.verify = False
    return _session


def _post_form(path, data=None):
    """POST form data to a nimbus view. Retries on connection errors."""
    session = _get_session()
    url = urljoin(_get_nginx_url(), path)
    for retry in range(LOAD_DATA_RETRIES):
        try:
            resp = session.post(url, data=data or {}, allow_redirects=False)
            if resp.status_code not in (200, 301, 302):
                raise RuntimeError(f"POST {path} failed ({resp.status_code})")
            return resp
        except requests.ConnectionError:
            if retry + 1 >= LOAD_DATA_RETRIES:
                raise
            time.sleep(LOAD_DATA_RETRY_DELAY)


def _get_page(path):
    """GET a page. Retries on connection errors."""
    session = _get_session()
    url = urljoin(_get_nginx_url(), path)
    for retry in range(LOAD_DATA_RETRIES):
        try:
            return session.get(url, allow_redirects=True)
        except requests.ConnectionError:
            if retry + 1 >= LOAD_DATA_RETRIES:
                raise
            time.sleep(LOAD_DATA_RETRY_DELAY)


def _get_api(path):
    """GET a REST API endpoint, return parsed JSON."""
    session = _get_session()
    url = urljoin(_get_nginx_url(), path)
    for retry in range(LOAD_DATA_RETRIES):
        try:
            resp = session.get(url)
            return resp.json()
        except (json.JSONDecodeError, requests.ConnectionError):
            if retry + 1 >= LOAD_DATA_RETRIES:
                raise
            time.sleep(LOAD_DATA_RETRY_DELAY)


def _extract_slug_from_hx_redirect(resp):
    """Extract experiment slug from HX-Redirect: /nimbus/{slug}/summary/"""
    hx = resp.headers.get("HX-Redirect", "")
    (_, _nimbus, slug, *_rest) = PurePosixPath(hx).parts
    return slug


def _extract_branch_form_json(html):
    tag = 'id="branch-form-data" type="application/json">'
    parts = html.split(tag, 1)
    if len(parts) < 2:
        raise RuntimeError("Could not find branch-form-data JSON in page")
    return json.loads(parts[1].split("</script>", 1)[0])


def _build_branches_form_data(
    slug,
    feature_config_ids=None,
    reference_branch=None,
    is_rollout=False,
):
    """Build POST data for the branches update form."""
    resp = _get_page(f"/nimbus/{slug}/update_branches/")
    branches = _extract_branch_form_json(resp.text)

    data = {
        "branches-TOTAL_FORMS": str(len(branches)),
        "branches-INITIAL_FORMS": str(len(branches)),
        "branches-MIN_NUM_FORMS": "0",
        "branches-MAX_NUM_FORMS": "1000",
    }

    for form_idx, branch in enumerate(branches):
        prefix = f"branches-{form_idx}"

        data[f"{prefix}-id"] = str(branch["id"])
        data[f"{prefix}-name"] = branch["name"]
        data[f"{prefix}-description"] = branch["description"] or branch["name"]
        data[f"{prefix}-slug"] = branch["slug"]
        data[f"{prefix}-ratio"] = "1"

        if form_idx == 0 and reference_branch:
            for key in ("name", "description"):
                if key in reference_branch:
                    data[f"{prefix}-{key}"] = str(reference_branch[key])

        if is_rollout and form_idx != 0:
            data[f"{prefix}-DELETE"] = "on"

        feature_values = branch.get("feature_values", [])
        data[f"{prefix}-feature-value-TOTAL_FORMS"] = str(len(feature_values))
        data[f"{prefix}-feature-value-INITIAL_FORMS"] = str(len(feature_values))
        data[f"{prefix}-feature-value-MIN_NUM_FORMS"] = "0"
        data[f"{prefix}-feature-value-MAX_NUM_FORMS"] = "1000"
        for fv_idx, feature_value in enumerate(feature_values):
            data[f"{prefix}-feature-value-{fv_idx}-id"] = str(feature_value["id"])
            if form_idx == 0 and reference_branch and "feature_value" in reference_branch:
                data[f"{prefix}-feature-value-{fv_idx}-value"] = reference_branch[
                    "feature_value"
                ]
            else:
                data[f"{prefix}-feature-value-{fv_idx}-value"] = feature_value.get(
                    "value", "{}"
                )

        screenshots = branch.get("screenshots", [])
        data[f"{prefix}-screenshots-TOTAL_FORMS"] = str(len(screenshots))
        data[f"{prefix}-screenshots-INITIAL_FORMS"] = str(len(screenshots))
        data[f"{prefix}-screenshots-MIN_NUM_FORMS"] = "0"
        data[f"{prefix}-screenshots-MAX_NUM_FORMS"] = "1000"

    if feature_config_ids:
        data["feature_configs"] = [str(config_id) for config_id in feature_config_ids]

    if is_rollout:
        data["is_rollout"] = "on"

    return data


def _coerce_form_values(data):
    """Convert Python values to form POST values."""
    form_data = {}
    for key, val in data.items():
        if isinstance(val, bool):
            if val:
                form_data[key] = "on"
        elif isinstance(val, list):
            form_data[key] = val
        else:
            form_data[key] = str(val)
    return form_data


def _default_feature_config_ids(app):
    """Get the default 'no feature' config ID for an application."""
    slug = NO_FEATURE_SLUGS.get(app)
    if slug:
        feature_id = get_feature_id_as_string(slug, app)
        if feature_id:
            return [int(feature_id)]
    return []


def load_targeting_configs(app=BaseExperimentApplications.FIREFOX_DESKTOP.value):
    targeting_configs = json.loads(TARGETING_CONFIGS_PATH.read_text())
    return [
        item["value"]
        for item in targeting_configs
        if (
            BaseExperimentApplications.FIREFOX_DESKTOP.value in app
            and BaseExperimentApplications.FIREFOX_DESKTOP.value
            in item["applicationValues"]
        )
        or (
            BaseExperimentApplications.FIREFOX_DESKTOP.value not in app
            and BaseExperimentApplications.FIREFOX_DESKTOP.value
            not in item["applicationValues"]
        )
    ]


def get_feature_id_as_string(slug, app):
    feature_configs = json.loads(FEATURE_CONFIGS_PATH.read_text())
    for config in feature_configs:
        if config["slug"] == slug and config["application"] == app:
            return str(config["id"])


def load_experiment_data(slug):
    experiment = _get_api(f"/api/v6/experiments/{slug}/")
    if not experiment or "detail" in experiment:
        experiment = _get_api(f"/api/v6/draft-experiments/{slug}/")

    return {
        "targeting": experiment.get("targeting"),
        "recipe_json": json.dumps(experiment),
    }


def create_basic_experiment(
    name,
    app,
    targeting=None,
    is_rollout=False,
    audience_overrides=None,
    feature_config_ids=None,
    reference_branch=None,
):
    """Create an experiment with sensible defaults for all forms."""
    if targeting is None:
        targeting = load_targeting_configs()[0]

    resp = _post_form(
        "/nimbus/create/",
        {"name": name, "hypothesis": "Test hypothesis", "application": app},
    )
    slug = _extract_slug_from_hx_redirect(resp)
    if not slug:
        raise RuntimeError(
            f"Failed to extract slug from create response: {resp.text[:500]}"
        )

    _post_form(
        f"/nimbus/{slug}/update_overview/",
        {
            "name": name,
            "public_description": "Integration test experiment",
            "risk_brand": "False",
            "risk_message": "False",
            "risk_revenue": "False",
            "risk_partner_related": "False",
            "risk_ai": "False",
            "documentation_links-TOTAL_FORMS": "0",
            "documentation_links-INITIAL_FORMS": "0",
            "documentation_links-MIN_NUM_FORMS": "0",
            "documentation_links-MAX_NUM_FORMS": "1000",
        },
    )

    audience = {
        "targeting_config_slug": targeting,
        "population_percent": "100",
        "total_enrolled_clients": "55",
        "firefox_min_version": "120.!",
    }
    if "desktop" in app:
        audience["channels"] = ["nightly", "beta", "release"]
    else:
        audience["channel"] = "release"
    if audience_overrides:
        audience.update(audience_overrides)
    _post_form(f"/nimbus/{slug}/update_audience/", audience)

    branch_data = _build_branches_form_data(
        slug,
        feature_config_ids=feature_config_ids or _default_feature_config_ids(app),
        reference_branch=reference_branch,
        is_rollout=is_rollout,
    )
    _post_form(f"/nimbus/{slug}/update_branches/", branch_data)

    if reference_branch and "feature_value" in reference_branch:
        branch_data = _build_branches_form_data(
            slug,
            feature_config_ids=feature_config_ids or _default_feature_config_ids(app),
            reference_branch=reference_branch,
            is_rollout=is_rollout,
        )
        _post_form(f"/nimbus/{slug}/update_branches/", branch_data)

    return slug


AUDIENCE_FIELDS = {
    "channel",
    "channels",
    "countries",
    "exclude_countries",
    "exclude_languages",
    "exclude_locales",
    "excluded_experiments_branches",
    "firefox_max_version",
    "firefox_min_version",
    "is_first_run",
    "is_sticky",
    "languages",
    "locales",
    "population_percent",
    "proposed_duration",
    "proposed_enrollment",
    "proposed_release_date",
    "required_experiments_branches",
    "targeting_config_slug",
    "total_enrolled_clients",
}


def create_experiment(slug, app, data=None, targeting=None, is_rollout=False):
    data = data or {}
    audience_overrides = _coerce_form_values(
        {k: v for k, v in data.items() if k in AUDIENCE_FIELDS}
    )
    create_basic_experiment(
        slug,
        app,
        targeting=targeting,
        is_rollout=is_rollout or data.get("is_rollout", False),
        audience_overrides=audience_overrides or None,
        feature_config_ids=data.get("feature_config_ids"),
        reference_branch=data.get("reference_branch"),
    )


def update_experiment_audience(slug, audience_data):
    """Update the audience form on an existing draft experiment.

    Merges audience_data into the default desktop audience fields so Django
    form validation passes even when only one field is being changed.
    """
    defaults = {
        "targeting_config_slug": "",
        "population_percent": "100",
        "total_enrolled_clients": "55",
        "firefox_min_version": "120.!",
        "channels": ["nightly", "beta", "release"],
    }
    defaults.update(audience_data)
    _post_form(f"/nimbus/{slug}/update_audience/", defaults)


def end_experiment(slug):
    _post_form(f"/nimbus/{slug}/live-to-complete/")
    _post_form(f"/nimbus/{slug}/approve-end-experiment/")
