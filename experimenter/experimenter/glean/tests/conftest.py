import pytest
from django.conf import settings
from glean import testing


@pytest.fixture(scope="function", autouse=True)
def reset_glean():
    testing.reset_glean(
        application_id="experimenter-backend", application_version=settings.APP_VERSION
    )
