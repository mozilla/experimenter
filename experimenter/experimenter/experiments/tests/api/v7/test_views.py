import json

from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.api.v7.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.api.v6.test_views import (
    CachedViewSetTest,
)
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusExperimentViewSet(CachedViewSetTest):
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

        response = self.client.get(reverse("nimbus-experiment-rest-v7-list"))
        recipes = json.loads(response.content)
        self.assertEqual(
            sorted(recipe["slug"] for recipe in recipes),
            sorted(expected_slugs),
        )

    def test_get_nimbus_experiment_returns_expected_data(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            slug="test-rest-detail",
        )

        response = self.client.get(
            reverse("nimbus-experiment-rest-v7-detail", kwargs={"slug": experiment.slug}),
        )

        self.assertEqual(response.status_code, 200)
        recipes = json.loads(response.content)
        self.assertEqual(NimbusExperimentSerializer(experiment).data, recipes)

    VIEW_STATUSES = set(NimbusExperiment.Status) - {NimbusExperiment.Status.DRAFT}

    @parameterized.expand(sorted(VIEW_STATUSES))
    def test_filter_by_status(self, status):
        experiment = NimbusExperimentFactory.create(status=status)
        for excluded_status in self.VIEW_STATUSES - {status}:
            NimbusExperimentFactory.create(status=excluded_status)

        response = self.client.get(
            reverse("nimbus-experiment-rest-v7-list"),
            {"status": [status]},
        )

        recipes = json.loads(response.content)
        self.assertEqual([recipe["slug"] for recipe in recipes], [experiment.slug])

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
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
                application=NimbusExperiment.Application.DESKTOP,
                slug=f"{feature.slug}-exp",
                feature_configs=[feature],
            )

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            slug="multi-1",
            feature_configs=[features["nimbus-qa-1"], features["testFeature"]],
        )

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            slug="multi-2",
            feature_configs=[features["nimbus-qa-2"], features["testFeature"]],
        )

        expected_slugs_by_feature_id = {
            "nimbus-qa-1": ["nimbus-qa-1-exp", "multi-1"],
            "nimbus-qa-2": ["nimbus-qa-2-exp", "multi-2"],
            "testFeature": ["testFeature-exp", "multi-1", "multi-2"],
        }

        # Test querying for an individual feature ID.
        for feature_id, expected_slugs in expected_slugs_by_feature_id.items():
            response = self.client.get(
                reverse("nimbus-experiment-rest-v7-list"),
                {"feature_config": feature_id},
            )
            recipes = json.loads(response.content)
            self.assertEqual(
                sorted(recipe["slug"] for recipe in recipes),
                sorted(expected_slugs),
            )

        # Test querying for multiple feature IDs
        response = self.client.get(
            reverse("nimbus-experiment-rest-v7-list"),
            {"feature_config": ["nimbus-qa-1", "nimbus-qa-2"]},
        )
        self.assertEqual(response.status_code, 200)
        recipes = json.loads(response.content)
        self.assertEqual(
            sorted(recipe["slug"] for recipe in recipes),
            sorted(["nimbus-qa-1-exp", "nimbus-qa-2-exp", "multi-1", "multi-2"]),
        )

    def test_filter_by_application(self):
        for application in NimbusExperiment.Application.values:
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
                application=application,
                slug=f"{application}-experiment",
            )

        response = self.client.get(
            reverse("nimbus-experiment-rest-v7-list"),
            {
                "application": [
                    NimbusExperiment.Application.FENIX,
                    NimbusExperiment.Application.IOS,
                ]
            },
        )

        recipes = json.loads(response.content)
        self.assertEqual(
            sorted(recipe["slug"] for recipe in recipes),
            sorted(
                [
                    f"{application}-experiment"
                    for application in (
                        NimbusExperiment.Application.FENIX,
                        NimbusExperiment.Application.IOS,
                    )
                ]
            ),
        )
