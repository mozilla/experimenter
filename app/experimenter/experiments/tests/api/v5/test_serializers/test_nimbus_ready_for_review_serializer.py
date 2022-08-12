from django.test import TestCase
from parameterized import parameterized

from experimenter.base.tests.factories import CountryFactory, LanguageFactory
from experimenter.experiments.api.v5.serializers import NimbusReviewSerializer
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
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
            {"reference_branch": {"description": [NimbusConstants.ERROR_REQUIRED_FIELD]}},
        )

    def test_invalid_experiment_requires_min_version_less_than_max_version(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_83,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_95,
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
            firefox_max_version=NimbusExperiment.Version.FIREFOX_83,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_83,
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
            {"description": [NimbusConstants.ERROR_REQUIRED_FIELD]},
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
            serializer.errors["feature_config"],
            [NimbusConstants.ERROR_REQUIRED_FEATURE_CONFIG],
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
            NimbusConstants.ERROR_REQUIRED_QUESTION,
        )
        self.assertEqual(
            str(serializer.errors["risk_revenue"][0]),
            NimbusConstants.ERROR_REQUIRED_QUESTION,
        )
        self.assertEqual(
            str(serializer.errors["risk_brand"][0]),
            NimbusConstants.ERROR_REQUIRED_QUESTION,
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
            serializer.errors["feature_config"],
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
            serializer.errors["feature_config"],
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
            serializer.errors["reference_branch"]["feature_value"][0],
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
            serializer.errors["reference_branch"]["feature_value"][0].startswith(
                "Additional properties are not allowed"
            ),
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
        self.assertTrue(serializer.is_valid())
        self.assertTrue(
            serializer.warnings["reference_branch"]["feature_value"][0].startswith(
                "Additional properties are not allowed"
            ),
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
            serializer.errors["treatment_branches"][0]["feature_value"][0].startswith(
                "Additional properties are not allowed"
            ),
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

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.warnings), 1, serializer.warnings)
        self.assertTrue(
            serializer.warnings["treatment_branches"][0]["feature_value"][0].startswith(
                "Additional properties are not allowed"
            ),
            serializer.warnings,
        )

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

    def test_rollout_valid_version_support(self):
        desktop = NimbusExperiment.Application.DESKTOP
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=desktop,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_108,
            feature_configs=[NimbusFeatureConfigFactory(application=desktop)],
            is_sticky=False,
            is_rollout=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
        )
        experiment.save()
        for branch in experiment.treatment_branches:
            branch.delete()

        data = {
            "application": str(desktop),
            "is_sticky": "false",
            "is_rollout": "true",
            "targeting_config_slug": NimbusExperiment.TargetingConfig.MAC_ONLY.value,
            "changelog_message": "test changelog message",
            "channel": "",
            "firefox_min_version": NimbusExperiment.Version.FIREFOX_108.value,
        }
        serializer = NimbusReviewSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 0)

    def test_rollout_invalid_version_support(self):
        desktop = NimbusExperiment.Application.DESKTOP
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=desktop,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_50,
            feature_configs=[NimbusFeatureConfigFactory(application=desktop)],
            is_sticky=True,
            is_rollout=True,
            targeting_config_slug=NimbusExperiment.TargetingConfig.MAC_ONLY,
        )
        experiment.save()
        for branch in experiment.treatment_branches:
            branch.delete()

        data = {
            "application": str(desktop),
            "is_sticky": "true",
            "is_rollout": "true",
            "targeting_config_slug": NimbusExperiment.TargetingConfig.MAC_ONLY.value,
            "changelog_message": "test changelog message",
            "channel": "",
            "firefox_min_version": NimbusExperiment.Version.FIREFOX_50.value,
        }
        serializer = NimbusReviewSerializer(
            experiment, data=data, partial=True, context={"user": self.user}
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1)
        self.assertEqual(
            serializer.errors["is_rollout"][0],
            NimbusConstants.ERROR_ROLLOUT_VERSION_SUPPORT,
        )


class TestNimbusReviewSerializerMultiFeature(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.feature_without_schema = NimbusFeatureConfigFactory.create(
            schema=None,
            application=NimbusExperiment.Application.DESKTOP,
        )
        self.feature_with_schema = NimbusFeatureConfigFactory.create(
            schema=BASIC_JSON_SCHEMA,
            application=NimbusExperiment.Application.DESKTOP,
        )

    def test_serializer_feature_config_validation_application_mismatches_error(self):
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
            [
                "You must select a feature configuration from the drop down.",
            ],
        )

    def test_serializer_feature_config_validation_bad_json_value(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            is_sticky=True,
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
        feature_values_errors = [
            e
            for e in serializer.errors["reference_branch"]["feature_values"]
            if "value" in e
        ]
        self.assertEqual(len(feature_values_errors), 1)
        self.assertIn(
            "Unterminated string",
            feature_values_errors[0]["value"][0],
        )

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_104,
                False,
                False,
            ),
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_103,
                True,
                True,
            ),
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_103,
                False,
                True,
            ),
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_104,
                True,
                True,
            ),
        ]
    )
    def test_serializer_feature_enable_version_support_reference_branch(
        self, application, firefox_version, feature_enabled, expected_valid
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            firefox_min_version=firefox_version,
            application=application,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=None,
                    application=application,
                )
            ],
        )
        for feature_value in experiment.reference_branch.feature_values.all():
            feature_value.enabled = feature_enabled
            feature_value.value = (
                """\
                    {"bar": {"baz": "baz", "qux": 123}}""".strip()
                if feature_enabled
                else ""
            )
            feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertEqual(serializer.is_valid(), expected_valid)
        if not expected_valid:
            self.assertEqual(len(serializer.errors), 1)
            error = serializer.errors["reference_branch"].get("feature_enabled")
            self.assertEqual(error, NimbusConstants.ERROR_FEATURE_ENABLED)

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_104,
                False,
                False,
            ),
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_103,
                True,
                True,
            ),
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_103,
                False,
                True,
            ),
            (
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Version.FIREFOX_104,
                True,
                True,
            ),
        ]
    )
    def test_serializer_feature_enable_version_support_treatment_branches(
        self, application, firefox_version, feature_enabled, expected_valid
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            firefox_min_version=firefox_version,
            application=application,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    schema=None,
                    application=application,
                )
            ],
        )

        for feature_value in experiment.treatment_branches[0].feature_values.all():
            feature_value.enabled = feature_enabled
            feature_value.value = (
                """\
                    {"bar": {"baz": "baz", "qux": 123}}""".strip()
                if feature_enabled
                else ""
            )
            feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertEqual(serializer.is_valid(), expected_valid)
        if not expected_valid:
            self.assertEqual(len(serializer.errors), 1)
            error = serializer.errors["treatment_branches"][0].get("feature_enabled")
            self.assertIsNotNone(error)
            self.assertEqual(error, NimbusConstants.ERROR_FEATURE_ENABLED)

    def test_serializer_feature_config_validation_reference_value_schema_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            is_sticky=True,
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
        feature_values_errors = [
            e
            for e in serializer.errors["reference_branch"]["feature_values"]
            if "value" in e
        ]
        self.assertEqual(len(feature_values_errors), 1)
        self.assertTrue(
            feature_values_errors[0]["value"][0].startswith(
                "Additional properties are not allowed"
            ),
            serializer.errors,
        )

    def test_serializer_feature_config_validation_treatment_value_schema_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                self.feature_without_schema,
                self.feature_with_schema,
            ],
            is_sticky=True,
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
        feature_values_errors = [
            e
            for e in serializer.errors["treatment_branches"][0]["feature_values"]
            if "value" in e
        ]
        self.assertEqual(len(feature_values_errors), 1)
        self.assertTrue(
            feature_values_errors[0]["value"][0].startswith(
                "Additional properties are not allowed"
            ),
            serializer.errors,
        )

    def test_serializer_feature_config_validation_treatment_value_no_schema(self):
        feature1 = NimbusFeatureConfigFactory.create(
            schema=None,
            application=NimbusExperiment.Application.DESKTOP,
        )
        feature2 = NimbusFeatureConfigFactory.create(
            schema=None,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[feature1, feature2],
            is_sticky=True,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature1
        )
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=feature2
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
        self.assertTrue(serializer.is_valid())

    # Add schema warn logic for multifeature in #7028
    # def test_serializer_feature_config_validation_reference_value_schema_warn(self):
    #     experiment = NimbusExperimentFactory.create_with_lifecycle(
    #         NimbusExperimentFactory.Lifecycles.CREATED,
    #         status=NimbusExperiment.Status.DRAFT,
    #         application=NimbusExperiment.Application.DESKTOP,
    #         channel=NimbusExperiment.Channel.NO_CHANNEL,
    #         warn_feature_schema=True,
    #         feature_configs=[
    #             self.feature_without_schema,
    #             self.feature_with_schema,
    #         ],
    #     )

    #     reference_feature_value = experiment.reference_branch.feature_values.get(
    #         feature_config=self.feature_with_schema
    #     )
    #     reference_feature_value.value = """\
    #         {"DDirectMigrateSingleProfile": true}
    #     """.strip()
    #     reference_feature_value.save()

    #     treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
    #         feature_config=self.feature_with_schema
    #     )
    #     treatment_feature_value.value = """\
    #         {"directMigrateSingleProfile": true}
    #     """.strip()
    #     treatment_feature_value.save()

    #     serializer = NimbusReviewSerializer(
    #         experiment,
    #         data=NimbusReviewSerializer(
    #             experiment,
    #             context={"user": self.user},
    #         ).data,
    #         context={"user": self.user},
    #     )

    #     self.assertTrue(serializer.is_valid())
    #     self.assertTrue(
    #         serializer.warnings["reference_branch"]["feature_values"][1]["value"][
    #             0
    #         ].startswith("Additional properties are not allowed"),
    #         serializer.warnings,
    #     )
    #     self.assertEqual(len(serializer.warnings), 1, serializer.warnings)

    # def test_serializer_feature_config_validation_treatment_value_schema_warn(self):
    #     experiment = NimbusExperimentFactory.create_with_lifecycle(
    #         NimbusExperimentFactory.Lifecycles.CREATED,
    #         status=NimbusExperiment.Status.DRAFT,
    #         application=NimbusExperiment.Application.DESKTOP,
    #         channel=NimbusExperiment.Channel.NO_CHANNEL,
    #         warn_feature_schema=True,
    #         feature_configs=[
    #             NimbusFeatureConfigFactory.create(
    #                 schema=BASIC_JSON_SCHEMA,
    #                 application=NimbusExperiment.Application.DESKTOP,
    #             )
    #         ],
    #     )
    #     reference_feature_value = experiment.reference_branch.feature_values.get()
    #     reference_feature_value.value = """\
    #         {"directMigrateSingleProfile": true}
    #     """.strip()
    #     reference_feature_value.save()

    #     treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
    #     treatment_feature_value.value = """\
    #         {"DDirectMigrateSingleProfile": true}
    #     """.strip()
    #     treatment_feature_value.save()

    #     serializer = NimbusReviewSerializer(
    #         experiment,
    #         data=NimbusReviewSerializer(
    #             experiment,
    #             context={"user": self.user},
    #         ).data,
    #         context={"user": self.user},
    #     )

    #     self.assertTrue(serializer.is_valid())
    #     self.assertEqual(len(serializer.warnings), 1, serializer.warnings)
    #     self.assertTrue(
    #         serializer.warnings["treatment_branches"][0]["feature_value"][0].startswith(
    #             "Additional properties are not allowed"
    #         ),
    #         serializer.warnings,
    #     )
