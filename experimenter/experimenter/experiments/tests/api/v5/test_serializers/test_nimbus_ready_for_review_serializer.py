import datetime
import json
from itertools import chain, product

from django.test import TestCase
from parameterized import parameterized

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.api.v5.serializers import NimbusReviewSerializer
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    TEST_LOCALIZATIONS,
    NimbusBranchFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.openidc.tests.factories import UserFactory

BASIC_JSON_SCHEMA = """\
{
"$schema": "http://json-schema.org/draft-07/schema#",
"description": "Password autocomplete",
"type": "object",
"properties": {
    "directMigrateSingleProfile": {
    "description": "Should we directly migrate a single profile?",
    "type": "boolean"
    }
},
"additionalProperties": false
}
"""

REF_JSON_SCHEMA = """\
{
  "$id": "resource://test.schema.json",
  "$ref": "resource://test.schema.json#/$defs/Foo",
  "$defs": {
    "Foo": {
      "$id": "file:///foo.schema.json",
      "type": "object",
      "properties": {
        "bar": {
          "$ref": "file:///foo.schema.json#/$defs/Bar"
        }
      },
      "$defs": {
        "Bar": {
          "type": "object",
          "properties": {
            "baz": {
              "type": "string"
            },
            "qux": {
              "type": "integer"
            }
          }
        }
      }
    }
  }
}
"""


class TestNimbusReviewSerializerSingleFeature(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_valid_experiment_with_single_feature(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_valid_experiment_with_multiple_features(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                ),
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                ),
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_experiment_default_hypothesis(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
        )
        experiment.hypothesis = NimbusExperiment.HYPOTHESIS_DEFAULT
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"hypothesis": ["Hypothesis cannot be the default value."]},
        )

    def test_invalid_experiment_requires_reference_branch(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
        )
        experiment.reference_branch = None
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"reference_branch": ["This field may not be null."]},
        )

    def test_invalid_experiment_reference_branch_requires_description(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
        )
        experiment.reference_branch.description = ""
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {
                    "description": [NimbusExperiment.ERROR_REQUIRED_FIELD]
                }
            },
        )

    def test_invalid_experiment_requires_min_version_less_than_max_version(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_83,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_96,
            is_sticky=True,
        )
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "firefox_min_version": [NimbusExperiment.ERROR_FIREFOX_VERSION_MIN],
                "firefox_max_version": [NimbusExperiment.ERROR_FIREFOX_VERSION_MAX],
            },
        )

    def test_desktop_min_version_under_113_shows_warning(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_106,
            is_rollout=True,
            is_sticky=True,
        )
        for branch in experiment.treatment_branches:
            branch.delete()
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.warnings,
            {
                "firefox_min_version": [NimbusExperiment.ERROR_DESKTOP_ROLLOUT_VERSION],
            },
        )

    def test_desktop_min_version_over_113_no_warning(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_118,
            is_rollout=True,
            is_sticky=True,
        )
        for branch in experiment.treatment_branches:
            branch.delete()
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.warnings, {})

    def test_mobile_min_version_under_113_no_warning(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_106,
            is_rollout=True,
            is_sticky=True,
        )
        for branch in experiment.treatment_branches:
            branch.delete()
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.warnings, {})

    def test_valid_experiment_min_dot_version_less_than_max_version(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_9830,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_99,
            is_sticky=True,
        )
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_102,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_102,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_101,
            ),
        ]
    )
    def test_valid_experiments_supporting_languages_versions(
        self, application, firefox_version
    ):
        experiment_1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            is_sticky=True,
        )
        experiment_1.save()
        serializer_1 = NimbusReviewSerializer(
            experiment_1,
            data=NimbusReviewSerializer(
                experiment_1,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer_1.is_valid())
        # selected languages
        language = LanguageFactory.create()
        experiment_2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            languages=[language.id],
            is_sticky=True,
        )
        experiment_2.save()
        serializer_2 = NimbusReviewSerializer(
            experiment_2,
            data=NimbusReviewSerializer(
                experiment_2,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer_2.is_valid())

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_100,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_100,
            ),
        ]
    )
    def test_valid_experiments_with_all_languages(self, application, firefox_version):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            is_sticky=True,
        )
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_100,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_100,
            ),
        ]
    )
    def test_invalid_experiments_with_specific_languages(
        self, application, firefox_version
    ):
        language = LanguageFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            languages=[language.id],
            is_sticky=True,
        )
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())

        self.assertIn("languages", serializer.errors)

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_102,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_102,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_101,
            ),
        ]
    )
    def test_valid_experiments_supporting_countries_versions_default_as_all_countries(
        self, application, firefox_version
    ):
        experiment_1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            countries=[],
            is_sticky=True,
        )

        serializer_1 = NimbusReviewSerializer(
            experiment_1,
            data=NimbusReviewSerializer(
                experiment_1,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer_1.is_valid())

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_102,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_102,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_101,
            ),
        ]
    )
    def test_valid_experiments_supporting_countries_versions_selecting_specific_country(
        self, application, firefox_version
    ):
        # selected countries
        country = CountryFactory.create()
        experiment_1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            countries=[country.id],
            is_sticky=True,
        )

        serializer_1 = NimbusReviewSerializer(
            experiment_1,
            data=NimbusReviewSerializer(
                experiment_1,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer_1.is_valid())

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_100,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_100,
            ),
        ]
    )
    def test_valid_experiments_with_country_unsupported_version(
        self, application, firefox_version
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            countries=[],
            is_sticky=True,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_101,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_100,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_100,
            ),
        ]
    )
    def test_invalid_experiments_with_specific_countries(
        self, application, firefox_version
    ):
        country = CountryFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            countries=[country.id],
            is_sticky=True,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())

        self.assertIn("countries", serializer.errors)

    @parameterized.expand(
        [
            (
                NimbusExperiment.TargetingConfig.MAC_ONLY,
                True,
                True,
                0,
            ),
            (
                NimbusExperiment.TargetingConfig.MAC_ONLY,
                False,
                True,
                0,
            ),
            (
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
                False,
                False,
                1,
            ),
            (
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
                True,
                True,
                0,
            ),
        ]
    )
    def test_experiments_with_is_sticky_error(
        self, targeting_config, is_sticky, serializer_result, errors
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            targeting_config_slug=targeting_config,
            channel=NimbusExperiment.Channel.RELEASE,
            is_sticky=is_sticky,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertEqual(serializer_result, serializer.is_valid())

        self.assertEqual(len(serializer.errors), errors)
        if not serializer_result:
            self.assertIn("is_sticky", serializer.errors)

    def test_valid_experiment_allows_min_version_equal_to_max_version(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
            firefox_max_version=NimbusExperiment.MIN_REQUIRED_VERSION,
            is_sticky=True,
        )
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_invalid_experiment_requires_non_zero_population_percent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            population_percent=0.0,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors["population_percent"][0]),
            "Ensure this value is greater than or equal to 0.0001.",
        )

    def test_valid_experiment_minimum_population_percent(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            population_percent=0.0001,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_experiment_treatment_branch_requires_description(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
        )
        treatment_branch = NimbusBranchFactory.create(
            experiment=experiment, description=""
        )
        experiment.branches.add(treatment_branch)
        experiment.save()
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["treatment_branches"][1],
            {"description": [NimbusExperiment.ERROR_REQUIRED_FIELD]},
        )

    def test_invalid_experiment_missing_feature_config(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[],
            is_sticky=True,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["feature_configs"],
            [NimbusExperiment.ERROR_REQUIRED_FEATURE_CONFIG],
        )

    def test_invalid_experiment_risk_questions(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            risk_partner_related=None,
            risk_revenue=None,
            risk_brand=None,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors["risk_partner_related"][0]),
            NimbusExperiment.ERROR_REQUIRED_QUESTION,
        )
        self.assertEqual(
            str(serializer.errors["risk_revenue"][0]),
            NimbusExperiment.ERROR_REQUIRED_QUESTION,
        )
        self.assertEqual(
            str(serializer.errors["risk_brand"][0]),
            NimbusExperiment.ERROR_REQUIRED_QUESTION,
        )

    @parameterized.expand(
        [
            (True, NimbusExperiment.Application.DESKTOP),
            (False, NimbusExperiment.Application.FENIX),
            (False, NimbusExperiment.Application.IOS),
        ]
    )
    def test_channel_required_for_mobile(self, expected_valid, application):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[NimbusFeatureConfigFactory(application=application)],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertEqual(serializer.is_valid(), expected_valid, serializer.errors)
        if not expected_valid:
            self.assertIn("channel", serializer.errors)

    def test_serializer_feature_config_validation_application_mismatches_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=BASIC_JSON_SCHEMA,
                    application=NimbusExperiment.Application.IOS,
                )
            ],
            is_sticky=True,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["feature_configs"],
            [
                "Feature Config application ios does not "
                "match experiment application fenix."
            ],
        )

    def test_serializer_feature_config_validation_missing_feature_config(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            feature_configs=[],
            is_sticky=True,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["feature_configs"],
            ["You must select a feature configuration from the drop down."],
        )

    def test_serializer_feature_config_validation_bad_json_value(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=BASIC_JSON_SCHEMA,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
            is_sticky=True,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"directMigrateSingleProfile: true
        """.strip()
        reference_feature_value.save()

        treatment_branch_value = experiment.treatment_branches[0].feature_values.get()
        treatment_branch_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_branch_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Unterminated string",
            serializer.errors["reference_branch"]["feature_values"][0]["value"][0],
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_reference_value_schema_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=BASIC_JSON_SCHEMA,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(
            serializer.errors["reference_branch"]["feature_values"][0]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.errors,
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_reference_value_schema_warn(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            warn_feature_schema=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=BASIC_JSON_SCHEMA,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertTrue(
            serializer.warnings["reference_branch"]["feature_values"][0]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.warnings,
        )
        self.assertEqual(len(serializer.warnings), 1, serializer.warnings)

    def test_serializer_feature_config_validation_treatment_value_schema_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=BASIC_JSON_SCHEMA,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
            is_sticky=True,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertTrue(
            serializer.errors["treatment_branches"][0]["feature_values"][0]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.errors,
        )
        self.assertEqual(len(serializer.errors), 1)

    def test_serializer_feature_config_validation_treatment_value_schema_warn(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            warn_feature_schema=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=BASIC_JSON_SCHEMA,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(len(serializer.warnings), 1, serializer.warnings)
        self.assertTrue(
            serializer.warnings["treatment_branches"][0]["feature_values"][0]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.warnings,
        )

    def test_serializer_feature_config_validation_treatment_value_warn_returns_object(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            warn_feature_schema=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=BASIC_JSON_SCHEMA,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        treatment_branch = NimbusBranchFactory.create(
            experiment=experiment, description="dgdgd"
        )
        experiment.branches.add(treatment_branch)
        experiment.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.warnings), 1, serializer.warnings)
        self.assertTrue(
            serializer.warnings["treatment_branches"][0]["feature_values"][0]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.warnings,
        )

        self.assertTrue(serializer.warnings["treatment_branches"][1], {})

    def test_serializer_feature_config_validation_supports_ref_json_schema(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            warn_feature_schema=False,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=REF_JSON_SCHEMA,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {
            "bar": {
                "baz": "baz",
                "qux": 123
            }
            }
        """.strip()
        reference_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid())

    def test_serializer_feature_config_validation_treatment_value_no_schema(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=None,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_valid_branches_for_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            is_sticky=True,
            is_rollout=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
        )
        experiment.save()
        for branch in experiment.treatment_branches:
            branch.delete()
        data = {
            "application": NimbusExperiment.Application.DESKTOP,
            "is_sticky": "true",
            "is_rollout": "true",
            "targeting_config_slug": NimbusExperiment.TargetingConfig.MAC_ONLY,
            "firefox_min_version": NimbusExperiment.Version.FIREFOX_108,
            "changelog_message": "test changelog message",
            "channel": "",
        }
        serializer = NimbusReviewSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())

    def test_no_treatment_branches_for_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                NimbusFeatureConfigFactory(
                    application=NimbusExperiment.Application.DESKTOP
                )
            ],
            is_sticky=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
        )

        experiment.is_rollout = True
        experiment.save()

        for branch in experiment.treatment_branches:
            branch.delete()

        data = {
            "application": NimbusExperiment.Application.DESKTOP,
            "is_sticky": "false",
            "is_rollout": "true",
            "targeting_config_slug": NimbusExperiment.TargetingConfig.MAC_ONLY,
            "treatment_branches": [
                {"name": "treatment A", "description": "desc1", "ratio": 1},
                {"name": "treatment B", "description": "desc2", "ratio": 1},
            ],
            "changelog_message": "test changelog message",
            "channel": "",
        }
        serializer = NimbusReviewSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["treatment_branches"][0]["name"],
            [NimbusExperiment.ERROR_SINGLE_BRANCH_FOR_ROLLOUT],
        )

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_105,
                NimbusExperiment.TargetingConfig.URLBAR_FIREFOX_SUGGEST_DATA_COLLECTION_ENABLED,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_105,
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            ),
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_105,
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_105,
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_105,
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            ),
        ]
    )
    def test_rollout_valid_version_support(
        self, application, firefox_version, targeting_config
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            feature_configs=[NimbusFeatureConfigFactory(application=application)],
            is_sticky=True,
            is_rollout=True,
            targeting_config_slug=targeting_config,
        )
        experiment.save()
        for branch in experiment.treatment_branches:
            branch.delete()

        data = {
            "application": application,
            "is_sticky": "true",
            "is_rollout": "true",
            "targeting_config_slug": targeting_config,
            "changelog_message": "test changelog message",
            "channel": NimbusExperiment.Channel.RELEASE,
            "firefox_min_version": firefox_version,
        }
        serializer = NimbusReviewSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_101,
                NimbusExperiment.TargetingConfig.URLBAR_FIREFOX_SUGGEST_DATA_COLLECTION_ENABLED,
            ),
            (
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Version.FIREFOX_101,
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            ),
            (
                NimbusExperiment.Application.FOCUS_ANDROID,
                NimbusExperiment.Version.FIREFOX_101,
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            ),
            (
                NimbusExperiment.Application.IOS,
                NimbusExperiment.Version.FIREFOX_101,
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            ),
            (
                NimbusExperiment.Application.FOCUS_IOS,
                NimbusExperiment.Version.FIREFOX_101,
                NimbusExperiment.TargetingConfig.MOBILE_NEW_USERS,
            ),
        ]
    )
    def test_rollout_invalid_version_support(
        self, application, firefox_version, targeting_config
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            channel=NimbusExperiment.Channel.RELEASE,
            firefox_min_version=firefox_version,
            feature_configs=[NimbusFeatureConfigFactory(application=application)],
            is_sticky=True,
            is_rollout=True,
            targeting_config_slug=targeting_config,
        )
        experiment.save()
        for branch in experiment.treatment_branches:
            branch.delete()

        data = {
            "application": application,
            "is_sticky": "true",
            "is_rollout": "true",
            "targeting_config_slug": targeting_config,
            "changelog_message": "test changelog message",
            "channel": NimbusExperiment.Channel.RELEASE,
            "firefox_min_version": firefox_version,
        }
        serializer = NimbusReviewSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1)
        self.assertIn("is_rollout", serializer.errors)

    def test_invalid_experiment_with_branch_missing_feature_value(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=None,
                    application=NimbusExperiment.Application.DESKTOP,
                )
            ],
        )
        for feature_value in experiment.reference_branch.feature_values.all():
            feature_value.value = ""
            feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {
                    "feature_values": [{"value": ["This field may not be blank."]}]
                }
            },
        )

    def test_bucket_namespace_warning_for_dupe_rollouts(self):
        desktop = NimbusExperiment.Application.DESKTOP
        channel = NimbusExperiment.Channel.NIGHTLY
        targeting_config_slug = NimbusExperiment.TargetingConfig.MAC_ONLY
        feature_configs = [NimbusFeatureConfigFactory(application=desktop)]

        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=desktop,
            channel=channel,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            feature_configs=feature_configs,
            is_sticky=False,
            is_rollout=True,
            targeting_config_slug=targeting_config_slug,
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=desktop,
            channel=channel,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            feature_configs=feature_configs,
            is_sticky=False,
            is_rollout=True,
            targeting_config_slug=targeting_config_slug,
        )

        for branch in chain(
            experiment1.treatment_branches, experiment2.treatment_branches
        ):
            branch.delete()

        experiment1.save()
        experiment2.save()

        serializer = NimbusReviewSerializer(
            experiment2,
            data=NimbusReviewSerializer(
                experiment2,
                context={"user": self.user},
            ).data,
            partial=True,
            context={"user": self.user},
        )

        self.assertTrue(experiment1.is_rollout and experiment2.is_rollout)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.warnings["bucketing"],
            [NimbusExperiment.ERROR_BUCKET_EXISTS],
        )

    def test_bucket_namespace_warning_for_non_dupe_rollouts(self):
        lifecycle = NimbusExperimentFactory.Lifecycles.CREATED
        channel = NimbusExperiment.Channel.NIGHTLY
        feature_configs_fenix = [
            NimbusFeatureConfigFactory(application=NimbusExperiment.Application.FENIX)
        ]
        feature_configs_ios = [
            NimbusFeatureConfigFactory(application=NimbusExperiment.Application.IOS)
        ]
        targeting_config_slug = NimbusExperiment.TargetingConfig.MAC_ONLY

        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            application=NimbusExperiment.Application.FENIX,
            channel=channel,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            feature_configs=feature_configs_fenix,
            is_sticky=False,
            is_rollout=True,
            targeting_config_slug=targeting_config_slug,
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            application=NimbusExperiment.Application.IOS,
            channel=channel,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            feature_configs=feature_configs_ios,
            is_sticky=False,
            is_rollout=True,
            targeting_config_slug=targeting_config_slug,
        )

        for branch in chain(
            experiment1.treatment_branches, experiment2.treatment_branches
        ):
            branch.delete()

        experiment1.save()
        experiment2.save()

        serializer = NimbusReviewSerializer(
            experiment2,
            data=NimbusReviewSerializer(
                experiment2,
                context={"user": self.user},
            ).data,
            partial=True,
            context={"user": self.user},
        )

        self.assertTrue(experiment1.is_rollout and experiment2.is_rollout)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.warnings, {})

    def test_bucket_namespace_warning_for_experiments(self):
        lifecycle = NimbusExperimentFactory.Lifecycles.CREATED
        desktop = NimbusExperiment.Application.DESKTOP
        channel = NimbusExperiment.Channel.NIGHTLY
        feature_configs = [NimbusFeatureConfigFactory(application=desktop)]
        targeting_config_slug = NimbusExperiment.TargetingConfig.MAC_ONLY

        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            application=desktop,
            channel=channel,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            feature_configs=feature_configs,
            is_sticky=False,
            is_rollout=False,
            targeting_config_slug=targeting_config_slug,
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            application=desktop,
            channel=channel,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            feature_configs=feature_configs,
            is_sticky=False,
            is_rollout=False,
            targeting_config_slug=targeting_config_slug,
        )

        experiment1.save()
        experiment2.save()

        serializer = NimbusReviewSerializer(
            experiment2,
            data=NimbusReviewSerializer(
                experiment2,
                context={"user": self.user},
            ).data,
            partial=True,
            context={"user": self.user},
        )

        self.assertFalse(experiment1.is_rollout and experiment2.is_rollout)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.warnings, {})

    def test_substitute_localizations(self):
        value = {
            "foo": {
                "$l10n": {
                    "id": "foo-string",
                    "text": "foo text",
                    "comment": "foo comment",
                }
            },
            "bar": [
                {
                    "$l10n": {
                        "id": "bar-string",
                        "text": "bar text",
                        "comment": "bar comment",
                    },
                },
                "baz",
            ],
            "qux": {
                "quux": {
                    "$l10n": {
                        "id": "quux-string",
                        "text": "quux text",
                        "comment": "quux comment",
                    }
                },
                "corge": "corge",
            },
            "grault": "grault",
            "garply": None,
        }

        substitutions = {
            "foo-string": "localized foo",
            "bar-string": "localized bar",
            "quux-string": "localized quux",
        }

        result = NimbusReviewSerializer._substitute_localizations(
            value, substitutions, "en-US"
        )

        self.assertDictEqual(
            result,
            {
                "foo": "localized foo",
                "bar": ["localized bar", "baz"],
                "qux": {
                    "quux": "localized quux",
                    "corge": "corge",
                },
                "grault": "grault",
                "garply": None,
            },
        )

    def test_localized_valid(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        locale_en_ca = LocaleFactory.create(code="en-CA")
        locale_fr = LocaleFactory.create(code="fr")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us, locale_en_ca, locale_fr],
            is_localized=True,
            localizations=TEST_LOCALIZATIONS,
            is_sticky=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps(
            {
                "foo": {
                    "$l10n": {
                        "id": "foo-string",
                        "text": "foo text",
                        "comment": "foo comment",
                    }
                },
                "bar": {
                    "$l10n": {
                        "id": "bar-string",
                        "text": "bar text",
                        "comment": "bar comment",
                    }
                },
            }
        )
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_localized_with_invalid_json(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us],
            is_localized=True,
            localizations="""{"en-US": {"error": "missing quote}}""",
            is_sticky=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())

        self.assertEqual(list(serializer.errors.keys()), ["localizations"])
        self.assertEqual(len(serializer.errors["localizations"]), 1)
        self.assertTrue(
            serializer.errors["localizations"][0].startswith("Invalid JSON: ")
        )

    def test_localized_with_invalid_localization_locales(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        locale_en_ca = LocaleFactory.create(code="en-CA")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us, locale_en_ca],
            is_sticky=True,
            is_localized=True,
            localizations="""{"en-US": {}}""",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            partial=True,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"localizations": ["Experiment locale en-CA not present in localizations."]},
        )

    def test_localized_with_invalid_targeting_locales(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us],
            is_sticky=True,
            is_localized=True,
            localizations="""{"en-US": {}, "en-CA": {}}""",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            partial=True,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "localizations": [
                    "Localization locale en-CA does not exist in experiment locales.",
                ]
            },
        )

    def test_localized_with_invalid_localization_payload(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us],
            is_sticky=True,
            is_localized=True,
            localizations="""{"en-US": []}""",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            partial=True,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(list(serializer.errors.keys()), ["localizations"])
        self.assertEqual(len(serializer.errors["localizations"]), 1)
        self.assertTrue(
            serializer.errors["localizations"][0].startswith(
                "Localization schema validation error: "
            )
        )

    def test_localized_experiment_with_empty_locales(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[],
            is_sticky=True,
            is_localized=True,
            localizations="""{"en-US": {}}""",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            partial=True,
            context={"user": self.user},
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"locales": ["Locales must not be empty for a localized experiment."]},
        )

    def test_localized_with_invalid_min_version(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        locale_en_ca = LocaleFactory.create(code="en-CA")
        locale_fr = LocaleFactory.create(code="fr")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us, locale_en_ca, locale_fr],
            is_localized=True,
            is_sticky=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_112,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "firefox_min_version": [
                    NimbusConstants.ERROR_DESKTOP_LOCALIZATION_VERSION,
                ]
            },
        )

    @parameterized.expand(
        [
            (NimbusExperiment.Application.DESKTOP, True),
            (NimbusExperiment.Application.FENIX, False),
            (NimbusExperiment.Application.IOS, False),
            (NimbusExperiment.Application.FOCUS_ANDROID, False),
            (NimbusExperiment.Application.FOCUS_IOS, False),
            (NimbusExperiment.Application.KLAR_ANDROID, False),
            (NimbusExperiment.Application.KLAR_IOS, False),
        ]
    )
    def test_localized_with_application(self, application, valid):
        locale_en_us = LocaleFactory.create(code="en-US")
        locale_en_ca = LocaleFactory.create(code="en-CA")
        locale_fr = LocaleFactory.create(code="fr")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            locales=[locale_en_us, locale_en_ca, locale_fr],
            is_localized=True,
            localizations=TEST_LOCALIZATIONS,
            is_sticky=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )
        self.assertEqual(serializer.is_valid(), valid, serializer.errors)
        if not valid:
            self.assertEqual(
                serializer.errors,
                {
                    "application": [
                        "Localized experiments are only supported for Firefox Desktop."
                    ]
                },
            )

    def test_localized_with_missing_substitutions(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
            is_sticky=True,
            is_localized=True,
            localizations=json.dumps({"en-US": {}}),
        )
        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps(
            {
                "foo": {
                    "$l10n": {
                        "id": "foo-string",
                        "text": "foo text",
                        "comment": "foo comment",
                    }
                },
                "bar": {
                    "$l10n": {
                        "id": "bar-string",
                        "text": "bar text",
                        "comment": "bar comment",
                    }
                },
            }
        )
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "localizations": [
                    "Locale en-US is missing substitutions for IDs: bar-string, "
                    "foo-string"
                ]
            },
        )

    def test_localized_with_invalid_substitutions(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
            is_sticky=True,
            is_localized=True,
            localizations=json.dumps(
                {
                    "en-US": {
                        "foo-string": "foo text",
                    }
                }
            ),
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=BASIC_JSON_SCHEMA,
                    application=NimbusExperiment.Application.DESKTOP,
                ),
            ],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps(
            {
                "directMigrateSingleProfile": {
                    "$l10n": {
                        "id": "foo-string",
                        "text": "foo text",
                        "comment": "foo comment",
                    }
                }
            }
        )
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {
                    "feature_values": [
                        {
                            "value": [
                                (
                                    "Schema validation errors occured during locale "
                                    "substitution for locale en-US"
                                ),
                                "'foo text' is not of type 'boolean'",
                            ]
                        }
                    ]
                }
            },
        )

    @parameterized.expand(
        [
            (
                {},
                "$l10n object is missing 'id'",
            ),
            (
                {"id": "foo"},
                "$l10n id 'foo' must be at least 9 characters long",
            ),
            (
                {"id": "&&&&&&&&&"},
                "$l10n id '&&&&&&&&&' contains invalid characters; only alphanumeric "
                "characters and dashes are permitted",
            ),
            (
                {"id": "foo-string"},
                "$l10n object with id 'foo-string' is missing 'text'",
            ),
            (
                {"id": "foo-string", "text": "foo text"},
                "$l10n object with id 'foo-string' is missing 'comment'",
            ),
        ]
    )
    def test_localized_value_missing_keys(self, l10n_obj, error_msg):
        locale_en_us = LocaleFactory.create(code="en-US")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
            is_sticky=True,
            is_localized=True,
            localizations=json.dumps(
                {
                    "en-US": {
                        "foo": "foo text",
                    }
                }
            ),
        )
        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps(
            {
                "foo": {
                    "$l10n": l10n_obj,
                },
            }
        )
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"reference_branch": {"feature_values": [{"value": [error_msg]}]}},
            serializer.errors,
        )

    def test_not_localized_with_localizations(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            is_sticky=True,
            is_localized=False,
            localizations="",
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user", self.user},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_return_warning_for_proposed_release_date_when_not_first_run(self):
        release_date = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.RELEASE,
            is_sticky=True,
            is_first_run=False,
            proposed_release_date=release_date,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEquals(
            serializer.warnings,
            {
                "proposed_release_date": [NimbusExperiment.ERROR_FIRST_RUN_RELEASE_DATE],
            },
        )

    def test_return_valid_for_proposed_release_date_when_first_run(self):
        release_date = datetime.date.today()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.RELEASE,
            is_sticky=True,
            is_first_run=True,
            proposed_release_date=release_date,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.warnings, {})


class TestNimbusReviewSerializerMultiFeature(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.feature_without_schema = NimbusFeatureConfigFactory.create(
            slug="feature_without_schema",
            schema=None,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.feature_with_schema = NimbusFeatureConfigFactory.create(
            slug="feature_with_schema",
            schema=BASIC_JSON_SCHEMA,
            application=NimbusExperiment.Application.DESKTOP,
        )

    def test_feature_configs_application_mismatches_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=None,
                    application=NimbusExperiment.Application.FENIX,
                ),
                NimbusFeatureConfigFactory.create(
                    schema=None,
                    application=NimbusExperiment.Application.IOS,
                ),
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_94,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["feature_configs"],
            [
                "Feature Config application ios does not "
                "match experiment application fenix."
            ],
        )

    def test_feature_configs_missing_feature_config(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            feature_configs=[],
            is_sticky=True,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors["feature_configs"],
            [
                "You must select a feature configuration from the drop down.",
            ],
        )

    def test_feature_configs_reference_bad_json_value(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_95,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=self.feature_with_schema
        )
        reference_feature_value.value = """\
            {"directMigrateSingleProfile: true
        """.strip()
        reference_feature_value.save()

        treatment_branch_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_branch_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_branch_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1)
        self.assertIn(
            "Unterminated string",
            serializer.errors["reference_branch"]["feature_values"][1]["value"][0],
        )

    def test_feature_configs_treatment_bad_json_value(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_95,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=self.feature_with_schema
        )
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_branch_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_branch_value.value = """\
            {"directMigrateSingleProfile: true}
        """.strip()
        treatment_branch_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1, serializer.errors)
        self.assertIn(
            "Unterminated string",
            serializer.errors["treatment_branches"][0]["feature_values"][1]["value"][0],
        )

    def test_feature_configs_reference_value_schema_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=self.feature_with_schema
        )
        reference_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1)
        self.assertTrue(
            serializer.errors["reference_branch"]["feature_values"][1]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.errors,
        )

    def test_feature_configs_treatment_value_schema_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=self.feature_with_schema
        )
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1)
        self.assertTrue(
            serializer.errors["treatment_branches"][0]["feature_values"][1]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.errors,
        )

    def test_feature_configs_no_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            warn_feature_schema=False,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=self.feature_with_schema
        )
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": false}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_feature_configs_reference_value_schema_warn(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            warn_feature_schema=True,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=self.feature_with_schema
        )
        reference_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertTrue(
            serializer.warnings["reference_branch"]["feature_values"][1]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.warnings,
        )

    def test_feature_configs_treatment_value_schema_warn(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            warn_feature_schema=True,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=self.feature_with_schema
        )
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertTrue(
            serializer.warnings["treatment_branches"][0]["feature_values"][1]["value"][
                0
            ].startswith("Additional properties are not allowed"),
            serializer.warnings,
        )

    def test_feature_configs_no_warnings(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            warn_feature_schema=True,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=self.feature_with_schema
        )
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": false}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("reference_branch", serializer.warnings)
        self.assertNotIn("treatment_branch", serializer.warnings)

    def test_localized_valid(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        locale_en_ca = LocaleFactory.create(code="en-CA")
        locale_fr = LocaleFactory.create(code="fr")

        feature_a = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature_b = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us, locale_en_ca, locale_fr],
            is_localized=True,
            localizations=TEST_LOCALIZATIONS,
            is_sticky=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_113,
            feature_configs=[feature_a, feature_b],
        )
        for branch in experiment.treatment_branches:
            branch.delete()

        feature_a_value = experiment.reference_branch.feature_values.get(
            feature_config=feature_a
        )
        feature_a_value.value = json.dumps(
            {
                "foo": {
                    "$l10n": {
                        "id": "foo-string",
                        "text": "foo text",
                        "comment": "foo comment",
                    }
                },
            }
        )
        feature_a_value.save()

        feature_b_value = experiment.reference_branch.feature_values.get(
            feature_config=feature_b
        )
        feature_b_value.value = json.dumps(
            {
                "bar": {
                    "$l10n": {
                        "id": "bar-string",
                        "text": "bar text",
                        "comment": "bar comment",
                    }
                },
            }
        )
        feature_b_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    @parameterized.expand(
        product(
            list(NimbusExperiment.Application),
            (
                NimbusExperiment.Version.NO_VERSION,
                NimbusExperiment.Version.FIREFOX_95,
                NimbusExperiment.Version.FIREFOX_100,
            ),
        )
    )
    def test_minimum_version(self, application, firefox_min_version):
        valid_version = NimbusExperiment.Version.parse(
            firefox_min_version
        ) >= NimbusExperiment.Version.parse(NimbusExperiment.MIN_REQUIRED_VERSION)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            firefox_min_version=firefox_min_version,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )

        self.assertEqual(
            serializer.is_valid(),
            valid_version,
            serializer.errors if valid_version else "Experiment is invalid",
        )

        if not valid_version:
            self.assertEqual(
                serializer.errors,
                {
                    "firefox_min_version": [
                        NimbusExperiment.ERROR_FIREFOX_VERSION_MIN_96
                    ],
                },
            )

    @parameterized.expand(
        [
            (
                {
                    "toplevel": 1.2,
                },
            ),
            (
                {
                    "nested_list": [{"nested_value": 1.2}],
                },
            ),
            (
                {
                    "nested_dict": {"list": [1.2]},
                },
            ),
        ]
    )
    def test_feature_value_with_float_is_invalid(self, value):
        application = NimbusExperiment.Application.DESKTOP
        feature = NimbusFeatureConfigFactory.create(application=application, schema=None)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
        )
        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps(value)
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            NimbusExperiment.ERROR_NO_FLOATS_IN_FEATURE_VALUE,
            serializer.errors["reference_branch"]["feature_values"][0]["value"],
        )
