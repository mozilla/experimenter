import json
import os
import re
import time
from pathlib import Path

import requests

from nimbus.models.base_dataclass import (
    BaseExperimentApplications,
)

LOAD_DATA_RETRIES = 60
LOAD_DATA_RETRY_DELAY = 1.0
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
TARGETING_CONFIGS_PATH = FIXTURES_DIR / "targeting_configs.json"
FEATURE_CONFIGS_PATH = FIXTURES_DIR / "feature_configs.json"

# GraphQL app enum value -> Django model application slug
APP_SLUG_MAP = {
    "DESKTOP": "firefox-desktop",
    "FENIX": "fenix",
    "IOS": "ios",
}

# GraphQL camelCase -> Django form field name
OVERVIEW_FIELD_MAP = {
    "publicDescription": "public_description",
    "riskBrand": "risk_brand",
    "riskMessage": "risk_message",
    "riskRevenue": "risk_revenue",
    "riskPartnerRelated": "risk_partner_related",
    "riskAi": "risk_ai",
}

AUDIENCE_FIELD_MAP = {
    "targetingConfigSlug": "targeting_config_slug",
    "populationPercent": "population_percent",
    "totalEnrolledClients": "total_enrolled_clients",
    "firefoxMinVersion": "firefox_min_version",
    "firefoxMaxVersion": "firefox_max_version",
    "proposedEnrollment": "proposed_enrollment",
    "proposedDuration": "proposed_duration",
    "isSticky": "is_sticky",
    "channels": "channels",
    "channel": "channel",
    "locales": "locales",
    "countries": "countries",
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
                raise RuntimeError(
                    f"POST {path} failed ({resp.status_code}):\n{resp.text[:1000]}"
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
    """Extract experiment slug from HX-Redirect header."""
    hx = resp.headers.get("HX-Redirect", "")
    parts = [p for p in hx.split("/") if p]
    for i, part in enumerate(parts):
        if part == "nimbus" and i + 1 < len(parts):
            return parts[i + 1]
    return None


def _parse_branch_ids(html):
    """Parse branch form index and DB IDs from hidden inputs."""
    return re.findall(r'name="branches-(\d+)-id"[^>]*value="(\d+)"', html)


def _parse_field_value(html, field_name):
    """Parse a single hidden/text input value from HTML."""
    match = re.search(rf'name="{re.escape(field_name)}"[^>]*value="([^"]*)"', html)
    return match.group(1) if match else ""


def _build_branches_form_data(
    slug,
    feature_config_ids=None,
    reference_branch=None,
    treatment_branches=None,
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
        for field in ("name", "description", "ratio", "slug"):
            data[f"{prefix}-{field}"] = _parse_field_value(html, f"{prefix}-{field}")

        # Override reference branch (form index 0) if data provided
        if form_idx_str == "0" and reference_branch:
            for key in ("name", "description", "ratio"):
                if key in reference_branch:
                    data[f"{prefix}-{key}"] = str(reference_branch[key])

        # Mark non-reference branches for deletion if rollout
        if is_rollout and form_idx_str != "0":
            data[f"{prefix}-DELETE"] = "on"

        # Feature value sub-formset: preserve existing entries
        fv_ids = re.findall(
            rf'name="({prefix}-feature-value-(\d+)-id)"[^>]*value="(\d+)"', html
        )
        data[f"{prefix}-feature-value-TOTAL_FORMS"] = str(len(fv_ids))
        data[f"{prefix}-feature-value-INITIAL_FORMS"] = str(len(fv_ids))
        data[f"{prefix}-feature-value-MIN_NUM_FORMS"] = "0"
        data[f"{prefix}-feature-value-MAX_NUM_FORMS"] = "1000"
        for fv_name, fv_idx, fv_id in fv_ids:
            data[fv_name] = fv_id
            data[f"{prefix}-feature-value-{fv_idx}-value"] = _parse_field_value(
                html, f"{prefix}-feature-value-{fv_idx}-value"
            )

        # Screenshots sub-formset: preserve existing entries
        ss_ids = re.findall(
            rf'name="({prefix}-screenshots-(\d+)-id)"[^>]*value="(\d+)"', html
        )
        data[f"{prefix}-screenshots-TOTAL_FORMS"] = str(len(ss_ids))
        data[f"{prefix}-screenshots-INITIAL_FORMS"] = str(len(ss_ids))
        data[f"{prefix}-screenshots-MIN_NUM_FORMS"] = "0"
        data[f"{prefix}-screenshots-MAX_NUM_FORMS"] = "1000"

    if feature_config_ids:
        data["feature_configs"] = [str(fid) for fid in feature_config_ids]

    if is_rollout:
        data["is_rollout"] = "on"

    return data


def _map_audience_data(gql_data):
    """Map GraphQL audience field names to Django form field names."""
    form_data = {}
    for gql_key, form_key in AUDIENCE_FIELD_MAP.items():
        if gql_key in gql_data:
            val = gql_data[gql_key]
            if isinstance(val, bool):
                if val:
                    form_data[form_key] = "on"
            elif isinstance(val, list):
                form_data[form_key] = val
            else:
                form_data[form_key] = str(val)
    return form_data


def _map_overview_data(gql_data):
    """Map GraphQL overview field names to Django form field names."""
    form_data = {}
    for gql_key, form_key in OVERVIEW_FIELD_MAP.items():
        if gql_key in gql_data:
            val = gql_data[gql_key]
            if isinstance(val, bool):
                form_data[form_key] = "True" if val else "False"
            else:
                form_data[form_key] = str(val)
    return form_data


# --- Public API (same signatures as the old GraphQL-based functions) ---


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
    for f in feature_configs:
        if f["slug"] == slug and f["application"] == APP_SLUG_MAP.get(app, app):
            return str(f["id"])


def load_experiment_data(slug):
    # Try live experiments first, fall back to drafts
    experiment = _get_api(f"/api/v6/experiments/{slug}/")
    if not experiment or "detail" in experiment:
        experiment = _get_api(f"/api/v6/draft-experiments/{slug}/")

    return {
        "data": {
            "experimentBySlug": {
                "id": experiment.get("id"),
                "jexlTargetingExpression": experiment.get("targeting"),
                "recipeJson": json.dumps(experiment),
            }
        }
    }


def create_basic_experiment(name, app, targeting=None, languages=None, is_rollout=False):
    if targeting is None:
        targeting = load_targeting_configs()[0]

    app_slug = APP_SLUG_MAP.get(app, app)

    # Create the experiment via form POST
    resp = _post_form(
        "/nimbus/create/",
        {"name": name, "hypothesis": "Test hypothesis", "application": app_slug},
    )
    slug = _extract_slug_from_hx_redirect(resp)
    if not slug:
        raise RuntimeError(
            f"Failed to extract slug from create response: {resp.text[:500]}"
        )

    # Set targeting on audience form
    _post_form(
        f"/nimbus/{slug}/update_audience/",
        {"targeting_config_slug": targeting, "population_percent": "100"},
    )

    # Set rollout flag if needed
    if is_rollout:
        branch_data = _build_branches_form_data(slug, is_rollout=True)
        _post_form(f"/nimbus/{slug}/update_branches/", branch_data)

    return {"data": {"createExperiment": {"nimbusExperiment": {"slug": slug}}}}


def update_experiment(slug, data):
    # Overview fields
    overview_fields = {k: data[k] for k in OVERVIEW_FIELD_MAP if k in data}
    if overview_fields:
        form_data = _map_overview_data(overview_fields)
        # Name is required on the overview form — read it from the current page
        resp = _get_page(f"/nimbus/{slug}/update_overview/")
        name_match = re.search(r'name="name"[^>]*value="([^"]*)"', resp.text)
        if name_match:
            form_data["name"] = name_match.group(1)
        _post_form(f"/nimbus/{slug}/update_overview/", form_data)

    # Branch fields
    branch_keys = {
        "featureConfigIds",
        "referenceBranch",
        "treatmentBranches",
        "isRollout",
    }
    if branch_keys & data.keys():
        branch_data = _build_branches_form_data(
            slug,
            feature_config_ids=data.get("featureConfigIds"),
            reference_branch=data.get("referenceBranch"),
            treatment_branches=data.get("treatmentBranches"),
            is_rollout=data.get("isRollout", False),
        )
        _post_form(f"/nimbus/{slug}/update_branches/", branch_data)

    # Audience fields
    audience_fields = {k: data[k] for k in AUDIENCE_FIELD_MAP if k in data}
    if audience_fields:
        form_data = _map_audience_data(audience_fields)
        _post_form(f"/nimbus/{slug}/update_audience/", form_data)

    return {"data": {"updateExperiment": {"message": "success"}}}


def create_experiment(slug, app, data, targeting=None, is_rollout=False):
    return (
        create_basic_experiment(
            slug,
            app,
            targeting=targeting,
            is_rollout=is_rollout,
        ),
        update_experiment(slug, data),
    )


def end_experiment(slug):
    _post_form(f"/nimbus/{slug}/live-to-complete/")
    _post_form(f"/nimbus/{slug}/approve-end-experiment/")
