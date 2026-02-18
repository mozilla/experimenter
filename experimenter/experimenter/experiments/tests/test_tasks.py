import json
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from experimenter.experiments.api.cache import get_api_cache_key
from experimenter.experiments.tasks import _get_warm_cache_endpoints, warm_api_caches
from experimenter.experiments.tests.factories import NimbusExperimentFactory


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class TestWarmApiCaches(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def test_warm_api_caches_populates_cache_for_all_endpoints(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="live-experiment",
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            slug="draft-experiment",
        )

        warm_api_caches()

        for key_prefix, _, _ in _get_warm_cache_endpoints():
            cache_key = get_api_cache_key(key_prefix)
            cached = cache.get(cache_key)
            self.assertIsNotNone(cached, f"Cache for {key_prefix} should be populated")
            data = json.loads(cached)
            self.assertIsInstance(data, list)

    def test_warm_api_caches_contains_correct_experiments(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="live-experiment",
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            slug="draft-experiment",
        )

        warm_api_caches()

        # v6:experiments should contain the live experiment but not the draft
        v6_data = json.loads(cache.get(get_api_cache_key("v6:experiments")))
        v6_slugs = [exp["slug"] for exp in v6_data]
        self.assertIn("live-experiment", v6_slugs)
        self.assertNotIn("draft-experiment", v6_slugs)

        # v6:draft-experiments should contain the draft but not the live
        v6_draft_data = json.loads(cache.get(get_api_cache_key("v6:draft-experiments")))
        v6_draft_slugs = [exp["slug"] for exp in v6_draft_data]
        self.assertIn("draft-experiment", v6_draft_slugs)
        self.assertNotIn("live-experiment", v6_draft_slugs)

    def test_warm_api_caches_updates_stale_cache(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="experiment-1",
        )

        warm_api_caches()

        v6_data = json.loads(cache.get(get_api_cache_key("v6:experiments")))
        self.assertEqual(len([e for e in v6_data if e["slug"] == "experiment-1"]), 1)

        # Add another experiment and re-warm
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="experiment-2",
        )

        warm_api_caches()

        v6_data = json.loads(cache.get(get_api_cache_key("v6:experiments")))
        slugs = [exp["slug"] for exp in v6_data]
        self.assertIn("experiment-1", slugs)
        self.assertIn("experiment-2", slugs)

    def test_warm_api_caches_empty_db(self):
        warm_api_caches()

        for key_prefix, _, _ in _get_warm_cache_endpoints():
            cache_key = get_api_cache_key(key_prefix)
            cached = cache.get(cache_key)
            self.assertIsNotNone(cached)
            data = json.loads(cached)
            self.assertEqual(data, [])

    def test_warm_api_caches_first_run_endpoint(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="first-run-exp",
            is_first_run=True,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="not-first-run-exp",
            is_first_run=False,
        )

        warm_api_caches()

        first_run_data = json.loads(cache.get(get_api_cache_key("v6:first-run")))
        slugs = [exp["slug"] for exp in first_run_data]
        self.assertIn("first-run-exp", slugs)
        self.assertNotIn("not-first-run-exp", slugs)

    def test_all_api_versions_produce_valid_json(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="test-experiment",
        )

        warm_api_caches()

        for key_prefix, _, _ in _get_warm_cache_endpoints():
            cache_key = get_api_cache_key(key_prefix)
            cached = cache.get(cache_key)
            data = json.loads(cached)
            for exp in data:
                self.assertIn("slug", exp)
                self.assertIn("branches", exp)

    def test_warm_api_caches_raises_on_error(self):
        with (
            mock.patch(
                "experimenter.experiments.tasks.warm_api_cache",
                side_effect=Exception("serialization failed"),
            ),
            self.assertRaises(Exception),
        ):
            warm_api_caches()
