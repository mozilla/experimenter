import json
import os
import re
import time
from pathlib import Path, PurePosixPath

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
    url = f"{_get_nginx_url()}{path}"
    for retry in range(LOAD_DATA_RETRIES):
        try:
            resp = session.post(url, data=data or {}, allow_redirects=False)
            if resp.status_code not in (200, 301, 302):
                import re as _re

                error_detail = resp.text[:1000]
                exc_match = _re.search(r"Exception Value:.*?</td>", resp.text, _re.DOTALL)
                if exc_match:
                    error_detail = _re.sub(r"<[^>]+>", "", exc_match.group()).strip()
                tb_match = _re.search(
                    r'<textarea[^>]*id="traceback_area"[^>]*>(.*?)</textarea>',
                    resp.text,
                    _re.DOTALL,
                )
                if tb_match:
                    error_detail += "\n\n" + tb_match.group(1).strip()[:2000]
                raise RuntimeError(
                    f"POST {path} failed ({resp.status_code}):\n{error_detail}"
                )
            return resp
        except requests.ConnectionError:
            if retry + 1 >= LOAD_DATA_RETRIES:
                raise
            time.sleep(LOAD_DATA_RETRY_DELAY)


def _get_page(path):
    """GET a page. Retries on connection errors."""
    session = _get_session()
    url = f"{_get_nginx_url()}{path}"
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
    url = f"{_get_nginx_url()}{path}"
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


def _parse_field_value(html, field_name):
    """Parse a single hidden/text input value from HTML."""
    match = re.search(rf'name="{re.escape(field_name)}"[^>]*value="([^"]*)"', html)
    return match.group(1) if match else ""


def _parse_branch_ids(html):
    """Parse branch form index and DB IDs from hidden inputs."""
    return re.findall(r'name="branches-(\d+)-id"[^>]*value="(\d+)"', html)


def _build_branches_form_data(
    slug,
    feature_config_ids=None,
    reference_branch=None,
    is_rollout=False,
):
    """Build POST data for the branches update form by parsing the current page."""
    resp = _get_page(f"/nimbus/{slug}/update_branches/")
    html = resp.text
    branch_ids = _parse_branch_ids(html)

    data = {
        "branches-TOTAL_FORMS": str(len(branch_ids)),
        "branches-INITIAL_FORMS": str(len(branch_ids)),
        "branches-MIN_NUM_FORMS": "0",
        "branches-MAX_NUM_FORMS": "1000",
    }

    for form_idx_str, branch_id in branch_ids:
        prefix = f"branches-{form_idx_str}"

        data[f"{prefix}-id"] = branch_id
        for field in ("name", "description", "slug"):
            data[f"{prefix}-{field}"] = _parse_field_value(html, f"{prefix}-{field}")
        if not data[f"{prefix}-description"]:
            data[f"{prefix}-description"] = data[f"{prefix}-name"]
        data[f"{prefix}-ratio"] = "1"

        if form_idx_str == "0" and reference_branch:
            for key in ("name", "description"):
                if key in reference_branch:
                    data[f"{prefix}-{key}"] = str(reference_branch[key])

        if is_rollout and form_idx_str != "0":
            data[f"{prefix}-DELETE"] = "on"

        feature_value_ids = re.findall(
            rf'name="({prefix}-feature-value-(\d+)-id)"[^>]*value="(\d+)"', html
        )
        data[f"{prefix}-feature-value-TOTAL_FORMS"] = str(len(feature_value_ids))
        data[f"{prefix}-feature-value-INITIAL_FORMS"] = str(len(feature_value_ids))
        data[f"{prefix}-feature-value-MIN_NUM_FORMS"] = "0"
        data[f"{prefix}-feature-value-MAX_NUM_FORMS"] = "1000"
        for field_name, field_idx, field_id in feature_value_ids:
            data[field_name] = field_id
            data[f"{prefix}-feature-value-{field_idx}-value"] = _parse_field_value(
                html, f"{prefix}-feature-value-{field_idx}-value"
            )

        screenshot_ids = re.findall(
            rf'name="({prefix}-screenshots-(\d+)-id)"[^>]*value="(\d+)"', html
        )
        data[f"{prefix}-screenshots-TOTAL_FORMS"] = str(len(screenshot_ids))
        data[f"{prefix}-screenshots-INITIAL_FORMS"] = str(len(screenshot_ids))
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


def create_basic_experiment(name, app, targeting=None, languages=None, is_rollout=False):
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
    _post_form(f"/nimbus/{slug}/update_audience/", audience)

    branch_data = _build_branches_form_data(
        slug,
        feature_config_ids=_default_feature_config_ids(app),
        is_rollout=is_rollout,
    )
    _post_form(f"/nimbus/{slug}/update_branches/", branch_data)

    return slug


def update_experiment(slug, data):
    """Apply overrides to an already-created experiment."""
    if not data:
        return

    form_data = _coerce_form_values(data)

    resp = _get_page(f"/nimbus/{slug}/update_overview/")
    form_data["name"] = _parse_field_value(resp.text, "name")
    form_data["documentation_links-TOTAL_FORMS"] = "0"
    form_data["documentation_links-INITIAL_FORMS"] = "0"
    form_data["documentation_links-MIN_NUM_FORMS"] = "0"
    form_data["documentation_links-MAX_NUM_FORMS"] = "1000"
    _post_form(f"/nimbus/{slug}/update_overview/", form_data)

    branch_data = _build_branches_form_data(
        slug,
        feature_config_ids=data.get("feature_config_ids"),
        reference_branch=data.get("reference_branch"),
        is_rollout=data.get("is_rollout", False),
    )
    _post_form(f"/nimbus/{slug}/update_branches/", branch_data)

    _post_form(f"/nimbus/{slug}/update_audience/", form_data)


def create_experiment(slug, app, data=None, targeting=None, is_rollout=False):
    create_basic_experiment(
        slug,
        app,
        targeting=targeting,
        is_rollout=is_rollout,
    )
    update_experiment(slug, data or {})


def end_experiment(slug):
    _post_form(f"/nimbus/{slug}/live-to-complete/")
    _post_form(f"/nimbus/{slug}/approve-end-experiment/")
