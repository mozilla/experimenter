from django.core.cache import cache
from django.test import TestCase, override_settings
from mozilla_nimbus_schemas.jetstream import SampleSizesFactory

from experimenter.settings import SIZING_DATA_KEY


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    },
)
class MockSizingDataMixin(TestCase):
    sizing_test_data = None

    def setUp(self):
        super().setUp()
        cache.clear()

    def setup_cached_sizing_data(self):
        self.sizing_test_data = SampleSizesFactory.build()
        cache.set(SIZING_DATA_KEY, self.sizing_test_data)

    def get_cached_sizing_data(self):
        return self.sizing_test_data
