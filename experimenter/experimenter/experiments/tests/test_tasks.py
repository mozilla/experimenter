import json
from unittest import mock

from django.core.cache import cache
from django.http import QueryDict
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.renderers import JSONRenderer

from experimenter.experiments.api.cache import (
    get_api_cache_key,
    stream_render_queryset,
)
from experimenter.experiments.api.cache import warm_api_cache as real_warm_api_cache
from experimenter.experiments.api.v8.serializers import (
    NimbusExperimentSerializer as V8NimbusExperimentSerializer,
)
from experimenter.experiments.api.v8.views import NimbusExperimentViewSet as V8ViewSet
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tasks import (
    _get_warm_cache_endpoints,
    warm_api_cache_endpoint,
    warm_api_caches,
)
from experimenter.experiments.tests.factories import NimbusExperimentFactory


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    },
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
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

        for endpoint in _get_warm_cache_endpoints():
            cache_key = get_api_cache_key(endpoint.key_prefix, QueryDict(endpoint.params))
            cached = cache.get(cache_key)
            self.assertIsNotNone(cached, f"Cache for {endpoint.name} should be populated")

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

        for endpoint in _get_warm_cache_endpoints():
            cache_key = get_api_cache_key(endpoint.key_prefix, QueryDict(endpoint.params))
            cached = cache.get(cache_key)
            self.assertIsNotNone(cached)

    def test_warm_api_caches_json_endpoints_produce_valid_json(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="test-experiment",
        )

        warm_api_caches()

        json_endpoints = [
            endpoint
            for endpoint in _get_warm_cache_endpoints()
            if not endpoint.key_prefix.startswith("v5:")
        ]
        for endpoint in json_endpoints:
            cache_key = get_api_cache_key(endpoint.key_prefix, QueryDict(endpoint.params))
            cached = cache.get(cache_key)
            data = json.loads(cached)
            for exp in data:
                self.assertIn("slug", exp)
                self.assertIn("branches", exp)

    def test_warm_api_caches_v5_csv_endpoint(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="csv-experiment",
        )

        warm_api_caches()

        cached = cache.get(get_api_cache_key("v5:csv"))
        self.assertIsNotNone(cached)
        content = cached.decode("utf-8") if isinstance(cached, bytes) else cached
        self.assertIn("csv-experiment", content)

    def test_warm_api_caches_dispatches_one_subtask_per_endpoint(self):
        with mock.patch(
            "experimenter.experiments.tasks.warm_api_cache_endpoint.delay"
        ) as mock_delay:
            warm_api_caches()

        dispatched_keys = [call.args[0] for call in mock_delay.call_args_list]
        expected_keys = [endpoint.name for endpoint in _get_warm_cache_endpoints()]
        self.assertEqual(sorted(dispatched_keys), sorted(expected_keys))

    def test_warm_api_caches_failed_subtask_does_not_block_other_subtasks(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="live-experiment",
        )

        def fake_warm(key_prefix, *args, **kwargs):
            if key_prefix == "v6:experiments":
                raise RuntimeError("simulated OOM for v6")
            return real_warm_api_cache(key_prefix, *args, **kwargs)

        with mock.patch(
            "experimenter.experiments.tasks.warm_api_cache", side_effect=fake_warm
        ):
            warm_api_caches()

        self.assertIsNone(cache.get(get_api_cache_key("v6:experiments")))
        for key_prefix in (
            "v5:csv",
            "v6:draft-experiments",
            "v7:experiments",
            "v8:experiments",
            "v8:draft-experiments",
        ):
            self.assertIsNotNone(
                cache.get(get_api_cache_key(key_prefix)),
                f"{key_prefix} should still be warmed when v6:experiments fails",
            )

    def test_warm_api_cache_endpoint_unknown_key_logs_and_returns(self):
        with self.assertLogs("experimenter.experiments.tasks", level="ERROR") as captured:
            warm_api_cache_endpoint("does-not-exist")
        self.assertTrue(any("Unknown cache endpoint" in line for line in captured.output))

    def test_warm_api_cache_endpoint_raises_on_warm_failure(self):
        with (
            mock.patch(
                "experimenter.experiments.tasks.warm_api_cache",
                side_effect=Exception("serialization failed"),
            ),
            self.assertRaises(Exception),
        ):
            warm_api_cache_endpoint("v6:experiments")

    def test_stream_render_queryset_matches_drf_json_renderer(self):
        for slug in ("eq-experiment-1", "eq-experiment-2", "eq-experiment-3"):
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
                slug=slug,
            )

        queryset = V8ViewSet.queryset
        streamed = stream_render_queryset(queryset, V8NimbusExperimentSerializer)

        rendered = JSONRenderer().render(
            V8NimbusExperimentSerializer(queryset.all(), many=True).data
        )

        self.assertEqual(streamed, rendered)

    def _create_filtered_variant_experiments(self):
        desktop = NimbusExperiment.Application.DESKTOP
        fenix = NimbusExperiment.Application.FENIX
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            slug="desktop-complete",
            application=desktop,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="desktop-live",
            application=desktop,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            slug="fenix-complete",
            application=fenix,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="fenix-first-run",
            application=fenix,
            is_first_run=True,
        )

    def _filtered_variant_requests(self):
        return [
            (
                "v6:experiments?status=Complete",
                "nimbus-experiment-rest-v6-list",
                {"status": NimbusExperiment.Status.COMPLETE},
                ["desktop-complete", "fenix-complete"],
            ),
            (
                "v6:experiments?application=firefox-desktop",
                "nimbus-experiment-rest-v6-list",
                {"application": NimbusExperiment.Application.DESKTOP},
                ["desktop-complete", "desktop-live"],
            ),
            (
                "v6:experiments?is_first_run=false",
                "nimbus-experiment-rest-v6-list",
                {"is_first_run": "false"},
                ["desktop-complete", "desktop-live", "fenix-complete"],
            ),
            (
                "v7:experiments?application=firefox-desktop&status=Complete",
                "nimbus-experiment-rest-v7-list",
                {
                    "application": NimbusExperiment.Application.DESKTOP,
                    "status": NimbusExperiment.Status.COMPLETE,
                },
                ["desktop-complete"],
            ),
            (
                "v8:experiments?application=firefox-desktop",
                "nimbus-experiment-rest-v8-list",
                {"application": NimbusExperiment.Application.DESKTOP},
                ["desktop-complete", "desktop-live"],
            ),
        ]

    def test_warm_api_caches_filtered_variants_cover_expected_requests(self):
        filtered_names = sorted(
            endpoint.name for endpoint in _get_warm_cache_endpoints() if endpoint.params
        )
        expected_names = sorted(
            name for name, _, _, _ in self._filtered_variant_requests()
        )
        self.assertEqual(filtered_names, expected_names)

    def test_warm_api_caches_filtered_variants_are_served_to_matching_requests(self):
        self._create_filtered_variant_experiments()

        warm_api_caches()
        NimbusExperiment.objects.all().delete()

        for name, url_name, params, expected_slugs in self._filtered_variant_requests():
            response = self.client.get(reverse(url_name), {**params, "cb": "123"})
            self.assertEqual(response.status_code, 200)
            slugs = sorted(recipe["slug"] for recipe in json.loads(response.content))
            self.assertEqual(slugs, expected_slugs, name)

    def test_warm_api_caches_filtered_variants_match_on_miss_render(self):
        self._create_filtered_variant_experiments()

        warm_api_caches()
        warmed = {
            endpoint.name: cache.get(
                get_api_cache_key(endpoint.key_prefix, QueryDict(endpoint.params))
            )
            for endpoint in _get_warm_cache_endpoints()
        }
        cache.clear()

        for name, url_name, params, _ in self._filtered_variant_requests():
            response = self.client.get(reverse(url_name), params)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, warmed[name], name)
