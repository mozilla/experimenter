import datetime
import json

import yaml
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.api.v5.serializers import NimbusExperimentCsvSerializer
from experimenter.experiments.api.v5.views import NimbusExperimentCsvRenderer
from experimenter.experiments.models import NimbusExperiment, Tag
from experimenter.experiments.tests.api.v5.test_serializers.mixins import (
    MockFmlErrorMixin,
)
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusFmlErrorDataClass,
)


class TestNimbusExperimentCsvListView(TestCase):
    def test_get_returns_csv_info_sorted_by_start_date(self):
        user_email = "user@example.com"
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment_1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date(2022, 5, 1),
            name="Experiment 1",
            application=application,
            feature_configs=[feature_config],
        )

        experiment_2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date(2020, 5, 1),
            name="Experiment 2",
            application=application,
            feature_configs=[feature_config],
        )

        experiment_3 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date(2019, 5, 1),
            name="Experiment 3",
            application=application,
            feature_configs=[feature_config],
        )

        experiment_4 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            start_date=datetime.date(2021, 5, 1),
            name="Experiment 4",
            application=application,
            feature_configs=[feature_config],
        )

        response = self.client.get(
            reverse("nimbus-experiments-csv"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = NimbusExperimentCsvRenderer().render(
            NimbusExperimentCsvSerializer(
                [experiment_1, experiment_4, experiment_2, experiment_3], many=True
            ).data,
            renderer_context={"header": NimbusExperimentCsvSerializer.Meta.fields},
        )

        self.assertEqual(csv_data, expected_csv_data)

    def test_get_returns_csv_filter_archived_experiments_info(self):
        user_email = "user@example.com"
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment_1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=datetime.date(2019, 5, 1),
            application=application,
            feature_configs=[feature_config],
        )

        # Archived experiment
        NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config], is_archived=True
        )
        response = self.client.get(
            reverse("nimbus-experiments-csv"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = NimbusExperimentCsvRenderer().render(
            NimbusExperimentCsvSerializer([experiment_1], many=True).data,
            renderer_context={"header": NimbusExperimentCsvSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)


class TestNimbusExperimentYamlListView(TestCase):
    def _get_yaml(self):
        response = self.client.get(
            reverse("nimbus-experiments-yaml"),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/yaml; charset=utf-8")
        return yaml.safe_load(response.content.decode("utf-8"))

    def test_returns_empty_for_no_complete_experiments(self):
        response = self.client.get(
            reverse("nimbus-experiments-yaml"),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "")

    def test_sorted_by_start_date_descending(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            start_date=datetime.date(2022, 5, 1),
            name="Experiment Alpha",
            application=application,
            feature_configs=[feature_config],
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            start_date=datetime.date(2020, 5, 1),
            name="Experiment Beta",
            application=application,
            feature_configs=[feature_config],
        )

        data = self._get_yaml()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Experiment Alpha")
        self.assertEqual(data[1]["name"], "Experiment Beta")

    def test_excludes_archived_and_non_complete(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            name="Complete Experiment",
            application=application,
            feature_configs=[feature_config],
        )
        NimbusExperimentFactory.create(
            name="Archived Experiment",
            application=application,
            feature_configs=[feature_config],
            is_archived=True,
            status=NimbusExperiment.Status.COMPLETE,
        )
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            name="Live Experiment",
            application=application,
            feature_configs=[feature_config],
        )

        data = self._get_yaml()
        names = [exp["name"] for exp in data]
        self.assertIn("Complete Experiment", names)
        self.assertNotIn("Archived Experiment", names)
        self.assertNotIn("Live Experiment", names)

    def test_yaml_contains_all_fields(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(
            application=application,
            name="Test Feature",
            slug="test-feature",
        )

        parent = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            name="Parent Experiment",
            slug="parent-experiment",
            application=application,
            feature_configs=[feature_config],
        )

        required_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            name="Required Experiment",
            slug="required-experiment",
            application=application,
            feature_configs=[feature_config],
        )

        excluded_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            name="Excluded Experiment",
            slug="excluded-experiment",
            application=application,
            feature_configs=[feature_config],
        )

        locale = Locale.objects.create(code="en-US", name="English (US)")
        country = Country.objects.create(code="US", name="United States")
        language = Language.objects.create(code="en", name="English")
        tag = Tag.objects.create(name="test-tag")

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            start_date=datetime.date(2022, 1, 1),
            name="Full Experiment",
            slug="full-experiment",
            public_description="A test experiment.",
            hypothesis="Testing improves quality.",
            application=application,
            feature_configs=[feature_config],
            parent=parent,
            risk_ai=True,
            qa_status=NimbusExperiment.QAStatus.GREEN,
            conclusion_recommendations=["RERUN", "GRADUATE"],
        )
        experiment.locales.add(locale)
        experiment.countries.add(country)
        experiment.languages.add(language)
        experiment.tags.add(tag)
        experiment.required_experiments.add(required_exp)
        experiment.excluded_experiments.add(excluded_exp)
        experiment.save()

        data = self._get_yaml()
        exp = next(e for e in data if e["slug"] == "full-experiment")

        # Basic fields
        self.assertEqual(exp["name"], "Full Experiment")
        self.assertEqual(exp["status"], "Complete")
        self.assertEqual(exp["application_display"], "Firefox Desktop")
        self.assertIn("full-experiment", exp["experiment_url"])

        # Parent
        self.assertEqual(
            exp["parent_experiment"], "Parent Experiment (parent-experiment)"
        )

        # Hypothesis (not default)
        self.assertEqual(exp["hypothesis"], "Testing improves quality.")

        # QA status (not NOT_SET)
        self.assertEqual(exp["qa_status"], NimbusExperiment.QAStatus.GREEN)

        # Locales/countries/languages
        self.assertEqual(exp["locales"]["codes"], ["en-US"])
        self.assertEqual(exp["countries"]["codes"], ["US"])
        self.assertEqual(exp["languages"]["codes"], ["en"])

        # Channels (desktop uses channels array)
        self.assertIsInstance(exp["channels"], list)

        # Tags
        self.assertIn("test-tag", exp["tags"])

        # Required/excluded experiments
        self.assertIn(
            "Required Experiment (required-experiment)",
            exp["required_experiments"],
        )
        self.assertIn(
            "Excluded Experiment (excluded-experiment)",
            exp["excluded_experiments"],
        )

        # Risk flags (risk_ai=True)
        self.assertIn("AI", exp["risk_flags"])

        # Conclusion recommendations
        self.assertIn("Rerun", exp["conclusion_recommendation_labels"])
        self.assertIn("Graduate", exp["conclusion_recommendation_labels"])

        # Feature configs
        slugs = [fc["slug"] for fc in exp["feature_configs"]]
        self.assertIn("test-feature", slugs)

    def test_default_hypothesis_excluded(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            hypothesis=NimbusExperiment.HYPOTHESIS_DEFAULT,
            application=application,
            feature_configs=[feature_config],
        )

        data = self._get_yaml()
        self.assertNotIn("hypothesis", data[0])

    def test_not_set_qa_status_excluded(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            qa_status=NimbusExperiment.QAStatus.NOT_SET,
            application=application,
            feature_configs=[feature_config],
        )

        data = self._get_yaml()
        self.assertNotIn("qa_status", data[0])

    def test_mobile_single_channel_fallback(self):
        application = NimbusExperiment.Application.FENIX
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[feature_config],
        )

        data = self._get_yaml()
        self.assertEqual(data[0]["channels"], [NimbusExperiment.Channel.RELEASE])

    def test_targeting_slug_fallback(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            feature_configs=[feature_config],
            targeting_config_slug="removed-targeting",
        )

        data = self._get_yaml()
        exp = next(e for e in data if e["slug"] == experiment.slug)
        self.assertEqual(exp["targeting"]["name"], "removed-targeting")

    def test_no_targeting_slug(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            feature_configs=[feature_config],
            targeting_config_slug="",
        )

        data = self._get_yaml()
        exp = next(e for e in data if e["slug"] == experiment.slug)
        self.assertNotIn("targeting", exp)


class TestFmlErrorsView(MockFmlErrorMixin, TestCase):
    def test_returns_fml_errors(self):
        user_email = "user@example.com"
        self.setup_get_fml_errors(
            [
                NimbusFmlErrorDataClass(
                    line=1,
                    col=0,
                    message="Incorrect value!",
                    highlight="enabled",
                ),
            ]
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
        )

        response = self.client.put(
            reverse("nimbus-fml-errors", kwargs={"slug": experiment.slug}),
            {"featureSlug": "blerp", "featureValue": json.dumps({"some": "value"})},
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            [
                {
                    "line": 1,
                    "col": 0,
                    "highlight": "enabled",
                    "message": "Incorrect value!",
                }
            ],
        )
