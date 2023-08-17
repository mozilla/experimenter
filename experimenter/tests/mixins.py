from django.core.cache import cache
from django.test import override_settings
from mozilla_nimbus_schemas.jetstream import SampleSizesFactory

from experimenter.settings import SIZING_DATA_KEY


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    },
)
class LocalDjangoCacheMixin(object):
    @classmethod
    def setUpClass(cls):
        super(LocalDjangoCacheMixin, cls).setUpClass()
        cache.clear()

    def _setup_cache_sizing(self):
        sizing_test_data = SampleSizesFactory.build()
        cache.set(SIZING_DATA_KEY, sizing_test_data)

    def get_cache_sizing(self):
        if sizing_data := cache.get(SIZING_DATA_KEY):
            return sizing_data
        self._setup_cache_sizing()
        return cache.get(SIZING_DATA_KEY)
