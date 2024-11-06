from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from mozilla_nimbus_schemas.jetstream import SampleSizesFactory


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

    def setup_cached_sizing_data(self, data=None):
        self.sizing_test_data = data
        if self.sizing_test_data is None:
            self.sizing_test_data = SampleSizesFactory.build().json()
        cache.set(settings.SIZING_DATA_KEY, self.sizing_test_data)

    def get_cached_sizing_data(self):
        return self.sizing_test_data
