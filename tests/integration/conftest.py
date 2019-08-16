import pytest
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


@pytest.fixture
def capabilities(capabilities):
    capabilities["acceptInsecureCerts"] = True
    return capabilities


@pytest.fixture
def firefox_options(firefox_options):
    """Set Firefox Options."""
    firefox_options.headless = True
    return firefox_options


@pytest.fixture(scope='session', autouse=True)
def _verify_url(request, base_url):
    """Verifies the base URL"""
    verify = request.config.option.verify_base_url
    if base_url and verify:
        session = requests.Session()
        retries = Retry(backoff_factor=0.1,
                        status_forcelist=[500, 502, 503, 504])
        session.mount(base_url, HTTPAdapter(max_retries=retries))
        session.get(base_url, verify=False)
