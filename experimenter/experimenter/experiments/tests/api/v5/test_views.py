import datetime
import json

import yaml
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
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


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class TestNimbusExperimentCsvListView(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

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


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class TestNimbusExperimentYamlListView(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def _get_yaml_response(self, page=None):
        url = reverse("nimbus-experiments-yaml")
        if page is not None:
            url = f"{url}?page={page}"
        response = self.client.get(
            url,
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/yaml; charset=utf-8")
        return yaml.safe_load(response.content.decode("utf-8"))

    def _get_yaml(self, page=None):
        parsed = self._get_yaml_response(page=page)
        if isinstance(parsed, dict) and "experiments" in parsed:
            return parsed["experiments"]
        return parsed

    def test_returns_empty_for_no_complete_experiments(self):
        parsed = self._get_yaml_response()
        self.assertEqual(parsed["count"], 0)
        self.assertEqual(parsed["experiments"], [])
        self.assertIsNone(parsed["next"])
        self.assertIsNone(parsed["previous"])

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
            results_data={
                "v3": {
                    "overall": {
                        "enrollments": {
                            "all": {
                                "control": {
                                    "branch_data": {
                                        "search_metrics": {
                                            "search_count": {
                                                "absolute": {
                                                    "all": [{"point": 10.0}],
                                                    "first": {},
                                                },
                                                "difference": {},
                                                "relative_uplift": {},
                                                "significance": {
                                                    "control": {"overall": {}},
                                                    "treatment": {
                                                        "overall": {"1": "positive"}
                                                    },
                                                },
                                            }
                                        }
                                    },
                                    "is_control": True,
                                }
                            }
                        }
                    },
                    "weekly": {"enrollments": {"all": {"control": {"branch_data": {}}}}},
                }
            },
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

        # Results data: only overall with significant metrics, weekly excluded
        rd = exp["results_data"]
        self.assertIn("overall", rd["v3"])
        self.assertNotIn("weekly", rd["v3"])
        search = rd["v3"]["overall"]["enrollments"]["all"]["control"]["branch_data"][
            "search_metrics"
        ]["search_count"]
        self.assertEqual(search["significance"]["treatment"]["overall"]["1"], "positive")

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

    def test_pagination_returns_metadata(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            feature_configs=[feature_config],
        )

        parsed = self._get_yaml_response()
        self.assertEqual(parsed["count"], 1)
        self.assertIsNone(parsed["next"])
        self.assertIsNone(parsed["previous"])
        self.assertEqual(len(parsed["experiments"]), 1)

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }
    )
    def test_pagination_multiple_pages(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        # Create 3 experiments; use page_size=2 via override
        for i in range(3):
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
                start_date=datetime.date(2020 + i, 1, 1),
                application=application,
                feature_configs=[feature_config],
            )

        with self.settings(YAML_EXPORT_PAGE_SIZE=2):
            from experimenter.experiments.api.v5.views import YamlExportPagination

            original_page_size = YamlExportPagination.page_size
            YamlExportPagination.page_size = 2
            try:
                cache.clear()
                page1 = self._get_yaml_response(page=1)
                self.assertEqual(page1["count"], 3)
                self.assertEqual(len(page1["experiments"]), 2)
                self.assertIsNotNone(page1["next"])
                self.assertIsNone(page1["previous"])

                page2 = self._get_yaml_response(page=2)
                self.assertEqual(page2["count"], 3)
                self.assertEqual(len(page2["experiments"]), 1)
                self.assertIsNone(page2["next"])
                self.assertIsNotNone(page2["previous"])

                # Ensure no overlap between pages
                page1_slugs = {e["slug"] for e in page1["experiments"]}
                page2_slugs = {e["slug"] for e in page2["experiments"]}
                self.assertEqual(len(page1_slugs & page2_slugs), 0)
            finally:
                YamlExportPagination.page_size = original_page_size

    def test_results_data_filters_to_overall_significant_only(self):
        """Results data should only include overall window and significant metrics."""
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)

        results_data = {
            "v3": {
                "overall": {
                    "enrollments": {
                        "all": {
                            "control": {
                                "branch_data": {
                                    "search_metrics": {
                                        "search_count": {
                                            "absolute": {
                                                "all": [
                                                    {
                                                        "point": 10.0,
                                                        "lower": 9.5,
                                                        "upper": 10.5,
                                                    }
                                                ],
                                                "first": {},
                                            },
                                            "difference": {
                                                "treatment": {
                                                    "all": [
                                                        {
                                                            "point": 0.5,
                                                            "lower": 0.1,
                                                            "upper": 0.9,
                                                        }
                                                    ]
                                                }
                                            },
                                            "relative_uplift": {
                                                "treatment": {
                                                    "all": [
                                                        {
                                                            "point": 0.05,
                                                            "lower": 0.01,
                                                            "upper": 0.09,
                                                        }
                                                    ]
                                                }
                                            },
                                            "significance": {
                                                "control": {"overall": {}},
                                                "treatment": {
                                                    "overall": {"1": "positive"}
                                                },
                                            },
                                        }
                                    },
                                    "other_metrics": {
                                        "neutral_metric": {
                                            "absolute": {
                                                "all": [{"point": 5.0}],
                                                "first": {},
                                            },
                                            "difference": {},
                                            "relative_uplift": {},
                                            "significance": {
                                                "control": {"overall": {}},
                                                "treatment": {
                                                    "overall": {"1": "neutral"}
                                                },
                                            },
                                        },
                                        "negative_metric": {
                                            "absolute": {
                                                "all": [{"point": 3.0}],
                                                "first": {},
                                            },
                                            "difference": {},
                                            "relative_uplift": {},
                                            "significance": {
                                                "control": {"overall": {}},
                                                "treatment": {
                                                    "overall": {"1": "negative"}
                                                },
                                            },
                                        },
                                    },
                                },
                                "is_control": True,
                            }
                        }
                    }
                },
                "weekly": {
                    "enrollments": {
                        "all": {
                            "control": {
                                "branch_data": {
                                    "search_metrics": {
                                        "search_count": {
                                            "absolute": {
                                                "all": [
                                                    {"point": 1.0, "window_index": "1"},
                                                    {"point": 2.0, "window_index": "2"},
                                                ],
                                                "first": {},
                                            },
                                            "significance": {},
                                        }
                                    }
                                },
                                "is_control": True,
                            }
                        }
                    }
                },
                "daily": {"enrollments": {"all": {}}},
                "other_metrics": {
                    "other_metrics": {
                        "neutral_metric": "Neutral",
                        "negative_metric": "Negative",
                    }
                },
            }
        }

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            name="Results Filter Test",
            slug="results-filter-test",
            application=application,
            feature_configs=[feature_config],
            results_data=results_data,
        )

        data = self._get_yaml()
        exp = next(e for e in data if e["slug"] == "results-filter-test")
        rd = exp["results_data"]

        # Only overall window is included
        self.assertIn("overall", rd["v3"])
        self.assertNotIn("weekly", rd["v3"])
        self.assertNotIn("daily", rd["v3"])

        branch = rd["v3"]["overall"]["enrollments"]["all"]["control"]

        # Significant metrics are kept
        self.assertIn("search_count", branch["branch_data"]["search_metrics"])
        self.assertIn("negative_metric", branch["branch_data"]["other_metrics"])

        # Neutral metrics are excluded
        self.assertNotIn("neutral_metric", branch["branch_data"]["other_metrics"])

        # other_metrics metadata is preserved
        self.assertIn("other_metrics", rd["v3"])

    def test_results_data_empty_or_missing_returns_none(self):
        """Null, missing v3, or missing overall return no results_data."""
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)

        for slug, rd in [
            ("no-results", None),
            ("no-v3", {"other_key": {}}),
            ("no-overall", {"v3": {"weekly": {}}}),
        ]:
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
                name=slug,
                slug=slug,
                application=application,
                feature_configs=[feature_config],
                results_data=rd,
            )

        data = self._get_yaml()
        for slug in ["no-results", "no-v3", "no-overall"]:
            exp = next(e for e in data if e["slug"] == slug)
            self.assertNotIn("results_data", exp)

    def test_results_data_all_neutral_returns_none(self):
        """Experiments with only neutral results should return None for results_data."""
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            name="All Neutral Experiment",
            slug="all-neutral-experiment",
            application=application,
            feature_configs=[feature_config],
            results_data={
                "v3": {
                    "overall": {
                        "enrollments": {
                            "all": {
                                "control": {
                                    "branch_data": {
                                        "other_metrics": {
                                            "some_metric": {
                                                "absolute": {
                                                    "all": [{"point": 5.0}],
                                                    "first": {},
                                                },
                                                "significance": {
                                                    "control": {"overall": {}},
                                                    "treatment": {
                                                        "overall": {"1": "neutral"}
                                                    },
                                                },
                                            }
                                        }
                                    },
                                    "is_control": True,
                                }
                            }
                        }
                    }
                }
            },
        )

        data = self._get_yaml()
        exp = next(e for e in data if e["slug"] == "all-neutral-experiment")
        # All metrics are neutral, so results_data stripped by _strip_empty
        self.assertNotIn("results_data", exp)


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
