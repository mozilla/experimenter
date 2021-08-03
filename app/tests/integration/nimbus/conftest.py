import os

import pytest
import requests
from nimbus.models.base_dataclass import (
    BaseAudienceDataClass,
    BaseBranchDataClass,
    BaseDataClass,
    BaseMetricsDataClass,
)
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


@pytest.fixture
def ds_issue_host():
    return os.environ["DS_ISSUE_HOST"]


@pytest.fixture
def capabilities(capabilities):
    capabilities["acceptInsecureCerts"] = True
    return capabilities


@pytest.fixture
def sensitive_url():
    pass


@pytest.fixture
def firefox_options(firefox_options):
    """Set Firefox Options."""
    firefox_options.log.level = "trace"
    return firefox_options


@pytest.fixture(scope="session", autouse=True)
def _verify_url(request, base_url):
    """Verifies the base URL"""
    verify = request.config.option.verify_base_url
    if base_url and verify:
        session = requests.Session()
        retries = Retry(backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        session.mount(base_url, HTTPAdapter(max_retries=retries))
        session.get(base_url, verify=False)


@pytest.fixture
def default_data():
    return BaseDataClass(
        hypothesis="smart stuff here",
        application="DESKTOP",
        public_description="description stuff",
        branches=[
            BaseBranchDataClass(
                name="name 1",
                description="a nice experiment",
                config="No Feature Firefox Desktop",
            )
        ],
        metrics=BaseMetricsDataClass(primary_outcomes=[], secondary_outcomes=[]),
        audience=BaseAudienceDataClass(
            channel="Nightly",
            min_version=80,
            targeting="TARGETING_MAC_ONLY",
            percentage=50.0,
            expected_clients=50,
        ),
    )
