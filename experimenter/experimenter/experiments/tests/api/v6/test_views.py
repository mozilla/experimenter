import json

from django.core.cache import cache
from django.http import QueryDict
from django.test import TestCase, override_settings
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.api.cache import get_api_cache_key
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tasks import warm_api_caches
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    },
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=False,
)
class CachedViewSetTest(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()


class NimbusExperimentFilterMixin:
    LIFECYCLE = NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
    LIST_VIEW = "nimbus-experiment-rest-v6-list"
    DETAIL_VIEW = "nimbus-experiment-rest-v6-detail"

    def create_experiment_kwargs(self):
        return {}

    def assert_returned_slugs(self, response, expected_slugs):
        self.assertEqual(response.status_code, 200)

        recipes = json.loads(response.content)
        self.assertEqual(
            sorted(recipe["slug"] for recipe in recipes),
            sorted(expected_slugs),
        )

    def test_filter_by_is_localized(self):
        NimbusExperimentFactory.create_with_lifecycle(
            self.LIFECYCLE,
            slug="experiment",
            **self.create_experiment_kwargs(),
        )
        NimbusExperimentFactory.create_with_lifecycle(
            self.LIFECYCLE,
            slug="localized_experiment",
            is_localized=True,
            localizations=json.dumps(
                {
                    "en-US": {},
                    "en-CA": {},
                }
            ),
            **self.create_experiment_kwargs(),
        )

        response = self.client.get(
            reverse(self.LIST_VIEW),
            {"is_localized": "True"},
        )
        self.assertEqual(response.status_code, 200)

        recipes = json.loads(response.content)
        slugs = [recipe["slug"] for recipe in recipes]

        self.assertEqual(slugs, ["localized_experiment"])

        response = self.client.get(
            reverse(self.LIST_VIEW),
            {"is_localized": "False"},
        )
        self.assertEqual(response.status_code, 200)

        recipes = json.loads(response.content)
        slugs = [recipe["slug"] for recipe in recipes]

        self.assertEqual(slugs, ["experiment"])

    def test_filter_by_feature_config(self):
        features = {
            slug: NimbusFeatureConfigFactory.create(
                slug=slug,
                application=NimbusExperiment.Application.DESKTOP,
            )
            for slug in ("testFeature", "nimbus-qa-1", "nimbus-qa-2")
        }

        for feature in features.values():
            NimbusExperimentFactory.create_with_lifecycle(
                self.LIFECYCLE,
                application=NimbusExperiment.Application.DESKTOP,
                slug=f"{feature.slug}-exp",
                feature_configs=[feature],
                **self.create_experiment_kwargs(),
            )

        NimbusExperimentFactory.create_with_lifecycle(
            self.LIFECYCLE,
            application=NimbusExperiment.Application.DESKTOP,
            slug="multi-1",
            feature_configs=[features["nimbus-qa-1"], features["testFeature"]],
            **self.create_experiment_kwargs(),
        )

        NimbusExperimentFactory.create_with_lifecycle(
            self.LIFECYCLE,
            application=NimbusExperiment.Application.DESKTOP,
            slug="multi-2",
            feature_configs=[features["nimbus-qa-2"], features["testFeature"]],
            **self.create_experiment_kwargs(),
        )

        expected_slugs_by_feature_id = {
            "nimbus-qa-1": ["nimbus-qa-1-exp", "multi-1"],
            "nimbus-qa-2": ["nimbus-qa-2-exp", "multi-2"],
            "testFeature": ["testFeature-exp", "multi-1", "multi-2"],
        }

        # Test querying for an individual feature ID.
        for feature_id, expected_slugs in expected_slugs_by_feature_id.items():
            response = self.client.get(
                reverse(self.LIST_VIEW),
                {"feature_config": feature_id},
            )
            self.assert_returned_slugs(response, expected_slugs)

        # Test querying for multiple feature IDs
        response = self.client.get(
            reverse(self.LIST_VIEW),
            {"feature_config": ["nimbus-qa-1", "nimbus-qa-2"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assert_returned_slugs(
            response, ["nimbus-qa-1-exp", "nimbus-qa-2-exp", "multi-1", "multi-2"]
        )

    def test_filter_by_application(self):
        for application in NimbusExperiment.Application.values:
            NimbusExperimentFactory.create_with_lifecycle(
                self.LIFECYCLE,
                application=application,
                slug=f"{application}-experiment",
                **self.create_experiment_kwargs(),
            )

        response = self.client.get(
            reverse(self.LIST_VIEW),
            {
                "application": [
                    NimbusExperiment.Application.FENIX,
                    NimbusExperiment.Application.IOS,
                ]
            },
        )

        self.assert_returned_slugs(
            response,
            [
                f"{application}-experiment"
                for application in (
                    NimbusExperiment.Application.FENIX,
                    NimbusExperiment.Application.IOS,
                )
            ],
        )


class NimbusExperimentIsFirstRunFilterMixin:
    def test_filter_by_is_first_run(self):
        first_run_experiment = NimbusExperimentFactory.create_with_lifecycle(
            self.LIFECYCLE,
            is_first_run=True,
            **self.create_experiment_kwargs(),
        )
        non_first_run_experiment = NimbusExperimentFactory.create_with_lifecycle(
            self.LIFECYCLE,
            is_first_run=False,
            **self.create_experiment_kwargs(),
        )

        response = self.client.get(reverse(self.LIST_VIEW), {"is_first_run": "True"})
        self.assert_returned_slugs(response, [first_run_experiment.slug])

        response = self.client.get(reverse(self.LIST_VIEW), {"is_first_run": "False"})
        self.assert_returned_slugs(response, [non_first_run_experiment.slug])


class TestNimbusExperimentViewSet(
    NimbusExperimentFilterMixin, NimbusExperimentIsFirstRunFilterMixin, CachedViewSetTest
):
    maxDiff = None

    def test_list_view_serializes_experiments(self):
        expected_slugs = []

        for lifecycle in NimbusExperimentFactory.Lifecycles:
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle, slug=lifecycle.name
            )

            if experiment.status not in [
                NimbusExperiment.Status.DRAFT,
            ]:
                expected_slugs.append(experiment.slug)

        response = self.client.get(reverse(self.LIST_VIEW))
        self.assert_returned_slugs(response, expected_slugs)

    def test_get_nimbus_experiment_returns_expected_data(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            slug="test-rest-detail",
        )

        response = self.client.get(
            reverse(self.DETAIL_VIEW, kwargs={"slug": experiment.slug}),
        )

        self.assertEqual(response.status_code, 200)
        recipes = json.loads(response.content)
        self.assertEqual(NimbusExperimentSerializer(experiment).data, recipes)


class TestNimbusExperimentDraftViewSet(
    NimbusExperimentFilterMixin, NimbusExperimentIsFirstRunFilterMixin, CachedViewSetTest
):
    maxDiff = None

    LIST_VIEW = "nimbus-experiment-rest-v6-draft-list"
    DETAIL_VIEW = "nimbus-experiment-rest-v6-draft-detail"
    LIFECYCLE = NimbusExperimentFactory.Lifecycles.CREATED

    def test_detail_view_serializes_draft_experiments(self):
        draft_slugs = []
        non_draft_slugs = []

        for lifecycle in NimbusExperimentFactory.Lifecycles:
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle,
                slug=lifecycle.name,
            )

            if experiment.status == NimbusExperiment.Status.DRAFT:
                draft_slugs.append(experiment.slug)
            else:
                non_draft_slugs.append(experiment.slug)

        for slug in draft_slugs:
            response = self.client.get(reverse(self.DETAIL_VIEW, kwargs={"slug": slug}))
            self.assertEqual(response.status_code, 200)

        for slug in non_draft_slugs:
            response = self.client.get(reverse(self.DETAIL_VIEW, kwargs={"slug": slug}))
            self.assertEqual(response.status_code, 404)

    def test_list_view_serializes_draft_experiments(self):
        expected_slugs = []

        for lifecycle in NimbusExperimentFactory.Lifecycles:
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle,
                slug=lifecycle.name,
            )

            if experiment.status == NimbusExperiment.Status.DRAFT:
                expected_slugs.append(experiment.slug)

        response = self.client.get(reverse(self.LIST_VIEW))
        self.assert_returned_slugs(response, expected_slugs)


class TestNimbusExperimentFirstRunViewSet(NimbusExperimentFilterMixin, CachedViewSetTest):
    maxDiff = None

    LIST_VIEW = "nimbus-experiment-rest-v6-first-run-list"
    DETAIL_VIEW = "nimbus-experiment-rest-v6-first-run-detail"

    def create_experiment_kwargs(self):
        return {"is_first_run": True}

    def test_list_view_serializes_live_first_run_experiments(self):
        expected_slugs = []

        for lifecycle in NimbusExperimentFactory.Lifecycles:
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                lifecycle,
                slug=lifecycle.name,
                **self.create_experiment_kwargs(),
            )

            if experiment.status == NimbusExperiment.Status.LIVE:
                expected_slugs.append(experiment.slug)

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING, is_first_run=False
        )

        response = self.client.get(reverse(self.LIST_VIEW))
        self.assert_returned_slugs(response, expected_slugs)


class TestCachedListBehavior(CachedViewSetTest):
    """Tests for the CachedListMixin serving responses from the warm cache."""

    def test_list_serves_from_warmed_cache(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="cached-experiment",
        )

        warm_api_caches()

        # Delete the experiment so the cache is the only source of data
        experiment.delete()

        response = self.client.get(reverse("nimbus-experiment-rest-v6-list"))
        self.assertEqual(response.status_code, 200)

        recipes = json.loads(response.content)
        slugs = [recipe["slug"] for recipe in recipes]
        self.assertIn("cached-experiment", slugs)

    def test_list_populates_cache_on_miss(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="fresh-experiment",
        )

        cache_key = get_api_cache_key("v6:experiments")
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get(reverse("nimbus-experiment-rest-v6-list"))
        self.assertEqual(response.status_code, 200)

        cached = cache.get(cache_key)
        self.assertIsNotNone(cached)
        data = json.loads(cached)
        slugs = [exp["slug"] for exp in data]
        self.assertIn("fresh-experiment", slugs)

    def test_list_caches_filtered_requests_separately(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="desktop-exp",
            application=NimbusExperiment.Application.DESKTOP,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="fenix-exp",
            application=NimbusExperiment.Application.FENIX,
        )

        # Request with filter — should cache separately
        response = self.client.get(
            reverse("nimbus-experiment-rest-v6-list"),
            {"application": NimbusExperiment.Application.DESKTOP},
        )
        self.assertEqual(response.status_code, 200)
        recipes = json.loads(response.content)
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0]["slug"], "desktop-exp")

        # Unfiltered request — should get all experiments
        response = self.client.get(reverse("nimbus-experiment-rest-v6-list"))
        self.assertEqual(response.status_code, 200)
        recipes = json.loads(response.content)
        slugs = sorted(recipe["slug"] for recipe in recipes)
        self.assertEqual(slugs, ["desktop-exp", "fenix-exp"])

    def test_list_ignores_unknown_params_and_serves_warmed_cache(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="cached-experiment",
        )

        warm_api_caches()
        experiment.delete()

        response = self.client.get(
            reverse("nimbus-experiment-rest-v6-list"),
            {"cb": "123", "limit": "10000", "bust-cache": "1"},
        )
        self.assertEqual(response.status_code, 200)

        recipes = json.loads(response.content)
        self.assertEqual([recipe["slug"] for recipe in recipes], ["cached-experiment"])

    def test_list_filter_with_unknown_params_shares_filter_cache_key(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            slug="complete-experiment",
        )

        response = self.client.get(
            reverse("nimbus-experiment-rest-v6-list"),
            {"status": NimbusExperiment.Status.COMPLETE},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(
            cache.get(
                get_api_cache_key(
                    "v6:experiments",
                    QueryDict(f"status={NimbusExperiment.Status.COMPLETE}"),
                )
            )
        )

        experiment.delete()

        response = self.client.get(
            reverse("nimbus-experiment-rest-v6-list"),
            {"status": NimbusExperiment.Status.COMPLETE, "cb": "123"},
        )
        self.assertEqual(response.status_code, 200)
        recipes = json.loads(response.content)
        self.assertEqual([recipe["slug"] for recipe in recipes], ["complete-experiment"])

    def test_list_real_filters_produce_distinct_cache_keys(self):
        self.client.get(
            reverse("nimbus-experiment-rest-v6-list"),
            {"application": NimbusExperiment.Application.DESKTOP, "cb": "1"},
        )
        self.client.get(
            reverse("nimbus-experiment-rest-v6-list"),
            {
                "application": [
                    NimbusExperiment.Application.DESKTOP,
                    NimbusExperiment.Application.FENIX,
                ],
                "cb": "2",
            },
        )

        desktop_key = get_api_cache_key(
            "v6:experiments",
            QueryDict(f"application={NimbusExperiment.Application.DESKTOP}"),
        )
        multi_key = get_api_cache_key(
            "v6:experiments",
            QueryDict(
                f"application={NimbusExperiment.Application.DESKTOP}"
                f"&application={NimbusExperiment.Application.FENIX}"
            ),
        )
        self.assertNotEqual(desktop_key, multi_key)
        self.assertIsNotNone(cache.get(desktop_key))
        self.assertIsNotNone(cache.get(multi_key))
        self.assertIsNone(cache.get(get_api_cache_key("v6:experiments")))

    @parameterized.expand(
        [
            (
                NimbusExperiment.Status.LIVE,
                NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            ),
            (
                NimbusExperiment.Status.PREVIEW,
                NimbusExperimentFactory.Lifecycles.PREVIEW,
            ),
        ]
    )
    def test_list_live_or_preview_filter_bypasses_cache(self, status, lifecycle):
        cache_key = get_api_cache_key("v6:experiments", QueryDict(f"status={status}"))
        cache.set(cache_key, b"[]")
        NimbusExperimentFactory.create_with_lifecycle(lifecycle, slug="fresh-experiment")

        response = self.client.get(
            reverse("nimbus-experiment-rest-v6-list"), {"status": status, "cb": "1"}
        )

        self.assertEqual(response.status_code, 200)
        recipes = json.loads(response.content)
        self.assertEqual([recipe["slug"] for recipe in recipes], ["fresh-experiment"])
        self.assertEqual(cache.get(cache_key), b"[]")

    def test_list_live_filter_with_other_filters_writes_nothing(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="desktop-live",
            application=NimbusExperiment.Application.DESKTOP,
        )
        params = {
            "application": NimbusExperiment.Application.DESKTOP,
            "status": NimbusExperiment.Status.LIVE,
        }

        response = self.client.get(reverse("nimbus-experiment-rest-v6-list"), params)

        self.assertEqual(response.status_code, 200)
        recipes = json.loads(response.content)
        self.assertEqual([recipe["slug"] for recipe in recipes], ["desktop-live"])
        query_params = QueryDict(mutable=True)
        query_params.update(params)
        self.assertIsNone(cache.get(get_api_cache_key("v6:experiments", query_params)))
