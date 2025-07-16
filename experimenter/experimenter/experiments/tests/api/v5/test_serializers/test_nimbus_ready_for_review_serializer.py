import datetime
import json
from itertools import chain, product
from typing import Literal, Optional, Union
from unittest.mock import patch

from django.test import TestCase
from parameterized import parameterized

import experimenter.experiments.constants
from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.api.v5.serializers import NimbusReviewSerializer
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment, NimbusFeatureVersion
from experimenter.experiments.tests.api.v5.test_serializers.mixins import (
    MockFmlErrorMixin,
)
from experimenter.experiments.tests.factories import (
    TEST_LOCALIZATIONS,
    NimbusBranchFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusFmlErrorDataClass,
    NimbusVersionedSchemaFactory,
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


class TestNimbusReviewSerializerSingleFeature(MockFmlErrorMixin, TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.setup_fml_no_errors()

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

    @parameterized.expand(
        [
            NimbusExperiment.Application.DESKTOP,
            NimbusExperiment.Application.FENIX,
            NimbusExperiment.Application.FOCUS_ANDROID,
            NimbusExperiment.Application.IOS,
            NimbusExperiment.Application.FOCUS_IOS,
        ]
    )
    def test_rollout_min_version_under_115_shows_warning(self, application):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_114,
            application=application,
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
                "firefox_min_version": [
                    NimbusExperiment.ERROR_ROLLOUT_VERSION.format(
                        application=NimbusExperiment.Application(application).label,
                        version=NimbusExperiment.Version.parse(
                            NimbusConstants.ROLLOUT_LIVE_RESIZE_MIN_SUPPORTED_VERSION[
                                application
                            ]
                        ),
                    )
                ],
            },
        )

    @parameterized.expand(
        [
            NimbusExperiment.Application.KLAR_IOS,
            NimbusExperiment.Application.KLAR_IOS,
        ]
    )
    def test_rollout_klar_min_version_under_115_no_warning(self, application):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
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

    @parameterized.expand(
        [
            NimbusExperiment.Application.DESKTOP,
            NimbusExperiment.Application.FENIX,
            NimbusExperiment.Application.FOCUS_ANDROID,
            NimbusExperiment.Application.IOS,
            NimbusExperiment.Application.FOCUS_IOS,
        ]
    )
    def test_rollout_min_version_over_115_no_warning(self, application):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_116,
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
            risk_message=None,
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
        self.assertEqual(
            str(serializer.errors["risk_message"][0]),
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
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.IOS,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=BASIC_JSON_SCHEMA,
                        ),
                    ],
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
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=BASIC_JSON_SCHEMA,
                        ),
                    ],
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
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=BASIC_JSON_SCHEMA,
                        ),
                    ],
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
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=BASIC_JSON_SCHEMA,
                        )
                    ],
                )
            ],
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true, "directMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = """\
            {"DDirectMigrateSingleProfile": true, "directMigrateSingleProfile": true}
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
        self.assertEqual(len(serializer.warnings), 2, serializer.warnings)

    def test_serializer_feature_config_validation_treatment_value_schema_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=BASIC_JSON_SCHEMA,
                        )
                    ],
                )
            ],
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
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
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=BASIC_JSON_SCHEMA,
                        ),
                    ],
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true, "DDirectMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true, "DDirectMigrateSingleProfile": true}
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
        self.assertEqual(len(serializer.warnings), 2, serializer.warnings)
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
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=BASIC_JSON_SCHEMA,
                        ),
                    ],
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = """\
            {"directMigrateSingleProfile": true, "DDirectMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true, "DDirectMigrateSingleProfile": true}
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
        self.assertEqual(len(serializer.warnings), 2, serializer.warnings)
        self.assertTrue(
            serializer.warnings["treatment_branches"][0]["feature_values"][0]["value"][
                0
            ].startswith("Additional properties are not allowed"),
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
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=REF_JSON_SCHEMA,
                        )
                    ],
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

        experiment.branches.exclude(id=experiment.reference_branch.id).delete()

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
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=None,
                        )
                    ],
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

    def test_serializer_fml_validation(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.FENIX,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=None,
                        )
                    ],
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = json.dumps({"bar": {"baz": "baz", "qux": 123}})

        reference_feature_value.save()

        experiment.branches.exclude(id=experiment.reference_branch.id).delete()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())

    def test_serializer_no_fml_validation_on_desktop(self):
        fml_errors = [
            NimbusFmlErrorDataClass(
                line=0,
                col=0,
                message="Incorrect value",
                highlight="enabled",
            ),
            NimbusFmlErrorDataClass(
                line=0,
                col=0,
                message="Type not allowed",
                highlight="record",
            ),
        ]
        self.setup_get_fml_errors(fml_errors)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=None,
                        )
                    ],
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = json.dumps({"bar": {"baz": "baz", "qux": 123}})
        reference_feature_value.save()

        experiment.branches.exclude(id=experiment.reference_branch.id).delete()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        self.assertTrue(serializer.is_valid())
        self.mock_fml_errors.assert_not_called()

    def test_serializer_fml_validation_on_cirrus(self):
        fml_errors = [
            NimbusFmlErrorDataClass(
                line=0,
                col=0,
                message="Incorrect value",
                highlight="enabled",
            ),
            NimbusFmlErrorDataClass(
                line=0,
                col=0,
                message="Type not allowed",
                highlight="record",
            ),
        ]
        self.setup_get_fml_errors(fml_errors)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DEMO_APP,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DEMO_APP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=None,
                        )
                    ],
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = json.dumps({"bar": {"baz": "baz", "qux": 123}})
        reference_feature_value.save()

        for branch in experiment.treatment_branches:
            branch.delete()

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
            set(serializer.errors["reference_branch"]["feature_values"][0]["value"]),
            {
                "In versions None-None: Incorrect value",
                "In versions None-None: Type not allowed",
            },
        )
        self.mock_fml_errors.assert_called()

    def test_serializer_fml_does_not_validate_desktop(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            warn_feature_schema=False,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=REF_JSON_SCHEMA,
                        )
                    ],
                )
            ],
            is_sticky=True,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )
        reference_feature_value = experiment.reference_branch.feature_values.get()
        reference_feature_value.value = json.dumps(
            {"bang": {"bong": "boom", "bing": "blang"}}
        )
        reference_feature_value.save()

        experiment.branches.exclude(id=experiment.reference_branch.id).delete()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid())
        self.mock_fml_errors.assert_not_called()
        self.assertEqual(len(serializer.errors), 0)

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
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=None,
                        )
                    ],
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
            firefox_min_version=NimbusExperiment.Version.FIREFOX_116,
            feature_configs=feature_configs_fenix,
            is_sticky=False,
            is_rollout=True,
            targeting_config_slug=targeting_config_slug,
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle,
            application=NimbusExperiment.Application.IOS,
            channel=channel,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_116,
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
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            schema=BASIC_JSON_SCHEMA,
                            version=None,
                        ),
                    ],
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
            context={"user": self.user},
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
        self.assertEqual(
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
        self.assertEqual(serializer.warnings, {})

    @parameterized.expand([("excluded_experiments",), ("required_experiments",)])
    def test_targeting_exclude_require_self(self, field):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_min_version=NimbusExperiment.EXCLUDED_REQUIRED_MIN_VERSION,
        )

        getattr(experiment, field).set([experiment])

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
                field: [NimbusExperiment.ERROR_EXCLUDED_REQUIRED_INCLUDES_SELF],
            },
        )

    @parameterized.expand(
        product(
            ("excluded_experiments", "required_experiments"),
            list(NimbusExperiment.Application),
            list(NimbusExperiment.Application),
        )
    )
    def test_targeting_exclude_require_application(self, field, app1, app2):
        other = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=app1,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=app2,
            firefox_min_version=NimbusExperiment.EXCLUDED_REQUIRED_MIN_VERSION,
            **{field: [other]},
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertEqual(
            serializer.is_valid(),
            app1 == app2,
            serializer.errors,
        )
        if app1 != app2:
            expected_error = (
                NimbusExperiment.ERROR_EXCLUDED_REQUIRED_DIFFERENT_APPLICATION
            )
            self.assertEqual(
                serializer.errors,
                {field: [expected_error.format(slug=other.slug)]},
            )

    @parameterized.expand(
        product(
            list(NimbusExperiment.Application),
            ("excluded_experiments", "required_experiments"),
        )
    )
    def test_targeting_exclude_require_min_version(self, application, field):
        other = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_115,
            **{field: [other]},
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )
        if NimbusExperiment.Application.is_web(application):
            self.assertTrue(serializer.is_valid())
        else:
            self.assertFalse(serializer.is_valid())

            self.assertEqual(
                serializer.errors,
                {
                    "firefox_min_version": [
                        NimbusExperiment.ERROR_EXCLUDED_REQUIRED_MIN_VERSION
                    ],
                },
            )

    def test_targeting_exclude_require_mutally_exclusive(self):
        other = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_min_version=NimbusExperiment.EXCLUDED_REQUIRED_MIN_VERSION,
            excluded_experiments=[other],
            required_experiments=[other],
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
            serializer.errors,
            {
                "excluded_experiments": [
                    NimbusExperiment.ERROR_EXCLUDED_REQUIRED_MUTUALLY_EXCLUSIVE,
                ],
                "required_experiments": [
                    NimbusExperiment.ERROR_EXCLUDED_REQUIRED_MUTUALLY_EXCLUSIVE,
                ],
            },
        )

    @parameterized.expand((False, True))
    def test_setpref_rollout_warning(self, prevent_pref_conflicts):
        self.maxDiff = None
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_min_version=NimbusExperiment.ROLLOUT_SUPPORT_VERSION[
                NimbusExperiment.Application.DESKTOP
            ],
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            is_rollout=True,
            prevent_pref_conflicts=prevent_pref_conflicts,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=None,
                            set_pref_vars={
                                "baz": "foo.bar.baz",
                            },
                        ),
                    ],
                ),
            ],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        if prevent_pref_conflicts:
            self.assertNotIn("pref_rollout_reenroll", serializer.warnings)
        else:
            self.assertEqual(
                serializer.warnings["pref_rollout_reenroll"],
                [NimbusExperiment.WARNING_ROLLOUT_PREF_REENROLL],
            )

    SET_PREF_WARNING_MSG = NimbusConstants.WARNING_LARGE_PREF.format(
        variable="foo",
        reason=NimbusConstants.SET_PREF_REASON,
    )
    SET_PREF_ERROR_MSG = NimbusConstants.ERROR_LARGE_PREF.format(
        variable="foo",
        reason=NimbusConstants.SET_PREF_REASON,
    )

    IS_EARLY_STARTUP_WARNING_MSG = NimbusConstants.WARNING_LARGE_PREF.format(
        variable="foo",
        reason=NimbusConstants.IS_EARLY_STARTUP_REASON.format(feature="feature"),
    )
    IS_EARLY_STARTUP_ERROR_MSG = NimbusConstants.ERROR_LARGE_PREF.format(
        variable="foo",
        reason=NimbusConstants.IS_EARLY_STARTUP_REASON.format(feature="feature"),
    )

    @parameterized.expand(
        [
            # No prefs set
            *(
                (None, schema_version, pref_type, pref_len, False, True, None, None)
                for schema_version in (None, 120)
                for pref_type in (str, list, dict)
                for pref_len in (0, 4097, 1024 * 1024 + 1)
            ),
            # Prefs <= 4kB do not cause any warnings or errors.
            *(
                (mode, schema_version, pref_type, 4096, False, True, None, None)
                for mode in ("setPref", "isEarlyStartup", "both")
                for schema_version in (None, 120)
                for pref_type in (str, list, dict)
            ),
            # Prefs > 4kB <= 1 mB cause errors when errors are not supressed.
            *(
                (mode, schema_version, pref_type, pref_len, False, False, None, msg)
                for mode, msg in (
                    ("setPref", SET_PREF_WARNING_MSG),
                    ("isEarlyStartup", IS_EARLY_STARTUP_WARNING_MSG),
                    ("both", IS_EARLY_STARTUP_WARNING_MSG),
                )
                for schema_version in (None, 120)
                for pref_type in (str, list, dict)
                for pref_len in (4097, 1024 * 1024)
            ),
            # Prefs > 4kB <= 1mB cause warnings when errors are suppressed.
            *(
                (mode, schema_version, pref_type, pref_len, True, True, msg, None)
                for mode, msg in (
                    ("setPref", SET_PREF_WARNING_MSG),
                    ("isEarlyStartup", IS_EARLY_STARTUP_WARNING_MSG),
                    ("both", IS_EARLY_STARTUP_WARNING_MSG),
                )
                for schema_version in (None, 120)
                for pref_type in (str, list, dict)
                for pref_len in (4097, 1024 * 1024)
            ),
            # Prefs > 1mB cause errors when errors are not supressed and cannot
            # be suppressed.
            *(
                (
                    mode,
                    schema_version,
                    pref_type,
                    1024 * 1024 + 1,
                    supress_errors,
                    False,
                    None,
                    msg,
                )
                for mode, msg in (
                    ("setPref", SET_PREF_ERROR_MSG),
                    ("isEarlyStartup", IS_EARLY_STARTUP_ERROR_MSG),
                    ("both", IS_EARLY_STARTUP_ERROR_MSG),
                )
                for schema_version in (None, 120)
                for pref_type in (str, list, dict)
                for supress_errors in (True, False)
            ),
        ]
    )
    def test_desktop_large_prefs(
        self,
        mode: Optional[
            Union[Literal["setPref"], Literal["isEarlyStartup"], Literal["both"]]
        ],
        schema_version: Optional[int],
        pref_type: type,
        value_len: int,
        suppress_errors: bool,
        expected_valid: bool,
        expected_warning: Optional[str],
        expected_error: Optional[str],
    ):
        self.assertIn(mode, (None, "setPref", "isEarlyStartup", "both"))

        set_pref_vars = {"bar": "pref.bar", "baz": "pref.baz"}
        if mode in ("setPref", "both"):
            set_pref_vars["foo"] = "pref.foo"

        is_early_startup = mode in ("isEarlyStartup", "both")
        schemas = [
            # An unversioned schema always exists.
            NimbusVersionedSchemaFactory.build(
                version=None,
                schema=None,
                is_early_startup=is_early_startup,
                set_pref_vars=set_pref_vars,
            ),
        ]

        if schema_version is not None:
            schemas.append(
                NimbusVersionedSchemaFactory.build(
                    version=NimbusFeatureVersion.objects.create(
                        major=schema_version,
                        minor=0,
                        patch=0,
                    ),
                    schema=None,
                    is_early_startup=is_early_startup,
                    set_pref_vars=set_pref_vars,
                ),
            )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.RELEASE,
            warn_feature_schema=suppress_errors,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.DESKTOP,
                    slug="feature",
                    name="feature",
                    schemas=schemas,
                ),
            ],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        # Ensure the serialized value is *exactly* value_len in length because
        # we are testing different thresholds
        if pref_type is str:
            foo_value = "a" * value_len
        else:
            self.assertIn(
                pref_type, (list, dict), "only str, list, dict supported for pref_type"
            )

            if pref_type is list:
                # But for values this short, we're always going to be under the
                # warning threshold, so it is ok if we bump it up slightly.
                if value_len <= 4:
                    value_len = 4

                foo_value = ["a" * (value_len - 4)]
            elif pref_type is dict:
                if value_len <= 9:
                    value_len = 9

                foo_value = {"a": "a" * (value_len - 9)}

            self.assertEqual(len(json.dumps(foo_value)), value_len)

        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps(
            {
                "foo": foo_value,
                "bar": 1,
                "baz": True,
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
        )

        if expected_valid:
            self.assertTrue(serializer.is_valid(), serializer.errors)
        else:
            self.assertFalse(serializer.is_valid())

        if expected_error is None:
            self.assertEqual(serializer.errors, {})
        else:
            if schema_version is not None:
                expected_error += f" at version {schema_version}.0.0"

            self.assertEqual(
                serializer.errors,
                {
                    "reference_branch": {
                        "feature_values": [
                            {
                                "value": [expected_error],
                            }
                        ],
                    },
                },
            )

        if expected_warning is None:
            self.assertEqual(serializer.warnings, {})
        else:
            if schema_version is not None:
                expected_warning += f" at version {schema_version}.0.0"

            self.assertEqual(
                serializer.warnings,
                {
                    "reference_branch": {
                        "feature_values": [
                            {
                                "value": [expected_warning],
                            }
                        ]
                    },
                },
            )

    def test_desktop_prefflips_channel_required(self):
        prefflips_feature = NimbusFeatureConfigFactory.create_desktop_prefflips_feature()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            feature_configs=[prefflips_feature],
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=prefflips_feature
        )
        feature_value.value = json.dumps({"prefs": {}})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"channel": [NimbusExperiment.ERROR_DESKTOP_PREFFLIPS_CHANNEL_REQUIRED]},
        )

    @parameterized.expand(
        (
            NimbusExperiment.Channel.UNBRANDED,
            NimbusExperiment.Channel.NIGHTLY,
            NimbusExperiment.Channel.BETA,
            NimbusExperiment.Channel.RELEASE,
            NimbusExperiment.Channel.ESR,
            NimbusExperiment.Channel.AURORA,
        )
    )
    def test_desktop_prefflips_feature_allowed_on_v128_esr_only(self, channel):
        prefflips_feature = NimbusFeatureConfigFactory.create_desktop_prefflips_feature()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_128,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            feature_configs=[prefflips_feature],
            channel=channel,
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=prefflips_feature
        )
        feature_value.value = json.dumps({"prefs": {}})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        if channel == NimbusExperiment.Channel.ESR:
            self.assertTrue(serializer.is_valid(), serializer.errors)
        else:
            self.assertFalse(serializer.is_valid())
            self.assertEqual(
                serializer.errors,
                {
                    "firefox_min_version": [
                        NimbusExperiment.ERROR_DESKTOP_PREFFLIPS_128_ESR_ONLY
                    ],
                },
            )

    @parameterized.expand(
        (
            NimbusExperiment.Channel.UNBRANDED,
            NimbusExperiment.Channel.NIGHTLY,
            NimbusExperiment.Channel.BETA,
            NimbusExperiment.Channel.RELEASE,
            NimbusExperiment.Channel.ESR,
            NimbusExperiment.Channel.AURORA,
        )
    )
    def test_desktop_prefflips_feature_allowed_on_v129(self, channel):
        prefflips_feature = NimbusFeatureConfigFactory.create_desktop_prefflips_feature()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            feature_configs=[prefflips_feature],
            channel=channel,
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=prefflips_feature
        )
        feature_value.value = json.dumps({"prefs": {}})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    @parameterized.expand(
        [
            ([(126, 0, 0)], None),
            ([(129, 1, 2)], "129.1.2"),
            ([(129, 0, 0), (129, 0, 1), (130, 0, 0)], "129.0.0-130.0.0"),
        ]
    )
    def test_desktop_prefflips_warns_setpref_conflicts(
        self, versions, formatted_versions
    ):
        pref = "foo.bar.baz"

        NimbusFeatureConfigFactory.create(
            name="test-feature",
            slug="test-feature",
            application=NimbusExperiment.Application.DESKTOP,
            schemas=[
                NimbusVersionedSchemaFactory.build(
                    set_pref_vars={"variable": pref},
                    version=NimbusFeatureVersion.objects.create(
                        major=major, minor=minor, patch=patch
                    ),
                )
                for (major, minor, patch) in versions
            ],
        )

        prefflips_feature = NimbusFeatureConfigFactory.create_desktop_prefflips_feature()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_129,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[prefflips_feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=prefflips_feature
        )
        feature_value.value = json.dumps(
            {"prefs": {pref: {"branch": "user", "value": "hello, world"}}}
        )
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        if formatted_versions is None:
            self.assertEqual(serializer.warnings, {})
        else:
            self.assertEqual(
                serializer.warnings,
                {
                    "reference_branch": {
                        "feature_values": [
                            {
                                "value": [
                                    NimbusConstants.WARNING_FEATURE_VALUE_IN_VERSIONS.format(
                                        versions=formatted_versions,
                                        warning=NimbusConstants.WARNING_PREF_FLIPS_PREF_CONTROLLED_BY_FEATURE.format(
                                            pref=pref, feature_config_slug="test-feature"
                                        ),
                                    )
                                ]
                            }
                        ]
                    }
                },
            )

    def test_empty_segments(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusConstants.MIN_REQUIRED_VERSION,
            segments=[],
        )

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)


class VersionedFeatureValidationTests(MockFmlErrorMixin, TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()

        self.user = UserFactory()

        self.versions = {
            (v.major, v.minor, v.patch): v
            for v in NimbusFeatureVersion.objects.bulk_create(
                NimbusFeatureVersion(major=major, minor=minor, patch=patch)
                for (major, minor, patch) in (
                    (120, 0, 0),
                    (121, 0, 0),
                    (122, 0, 0),
                    (123, 0, 0),
                )
            )
        }

    @parameterized.expand(
        [
            # min == max
            (NimbusExperiment.Version.FIREFOX_120, NimbusExperiment.Version.FIREFOX_120),
            (NimbusExperiment.Version.FIREFOX_121, NimbusExperiment.Version.FIREFOX_121),
            (NimbusExperiment.Version.FIREFOX_122, NimbusExperiment.Version.FIREFOX_122),
            # min <= max (bounded)
            (NimbusExperiment.Version.FIREFOX_120, NimbusExperiment.Version.FIREFOX_121),
            (NimbusExperiment.Version.FIREFOX_120, NimbusExperiment.Version.FIREFOX_122),
            (NimbusExperiment.Version.FIREFOX_121, NimbusExperiment.Version.FIREFOX_122),
            # min <= max (unbounded)
            (NimbusExperiment.Version.FIREFOX_120, NimbusExperiment.Version.NO_VERSION),
            (NimbusExperiment.Version.FIREFOX_121, NimbusExperiment.Version.NO_VERSION),
            (NimbusExperiment.Version.FIREFOX_122, NimbusExperiment.Version.NO_VERSION),
        ]
    )
    def test_validate_feature_range_valid(self, min_version, max_version):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)],
                    schema=BASIC_JSON_SCHEMA,
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(121, 0, 0)],
                    schema=BASIC_JSON_SCHEMA,
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)],
                    schema=BASIC_JSON_SCHEMA,
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=min_version,
            firefox_max_version=max_version,
            feature_configs=[feature],
            warn_feature_schema=False,
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature,
        )
        feature_value.value = json.dumps({"directMigrateSingleProfile": True})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    @parameterized.expand(
        chain(
            *(
                (
                    (
                        NimbusExperiment.Version.FIREFOX_120,
                        NimbusExperiment.Version.NO_VERSION,
                        NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_VERSIONS.format(
                            feature_config="FEATURE",
                            versions="121.0.0",
                        ),
                        as_warning,
                    ),
                    (
                        NimbusExperiment.Version.FIREFOX_121,
                        NimbusExperiment.Version.FIREFOX_121,
                        NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_RANGE.format(
                            feature_config="FEATURE",
                        ),
                        as_warning,
                    ),
                )
                for as_warning in (True, False)
            )
        )
    )
    def test_validate_feature_versioned_unsupported_versions(
        self, min_version, max_version, expected_error, as_warning
    ):
        """Testing feature validation with unsupported versions when using the
        warn_feature_schema compared to not using it
        """
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)], schema=None
                ),
            ],
        )

        NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(121, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)], schema=None
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=min_version,
            firefox_max_version=max_version,
            feature_configs=[feature],
            warn_feature_schema=as_warning,
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        if as_warning:
            self.assertTrue(serializer.is_valid(), serializer.errors)
            target = serializer.warnings
        else:
            self.assertFalse(serializer.is_valid())
            target = serializer.errors

        self.assertEqual(
            target,
            {
                "reference_branch": {
                    "feature_values": [
                        {
                            "value": [expected_error],
                        }
                    ]
                }
            },
            target,
        )

    def test_validate_feature_versioned_unsupported_multiple_versions(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(123, 0, 0)], schema=None
                ),
            ],
        )

        NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(121, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(123, 0, 0)], schema=None
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_123,
            feature_configs=[feature],
            warn_feature_schema=False,
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        error = NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_VERSIONS.format(
            feature_config="FEATURE",
            versions="121.0.0-122.0.0",
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {
                    "feature_values": [
                        {
                            "value": [error],
                        }
                    ]
                }
            },
        )

    @parameterized.expand(
        [
            (
                NimbusExperiment.Version.FIREFOX_110,
                NimbusExperiment.Version.NO_VERSION,
                [(122, 0, 0), (121, 0, 0), (120, 0, 0)],
            ),
            (
                NimbusExperiment.Version.FIREFOX_110,
                NimbusExperiment.Version.FIREFOX_120,
                [(120, 0, 0)],
            ),
        ]
    )
    def test_validate_feature_versioned_truncated_range_schema_errors(
        self, min_version, max_version, expected_versions
    ):
        schema = json.dumps(
            {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                    },
                },
                "additionalProperties": False,
            }
        )
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)],
                    schema=schema,
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(121, 0, 0)],
                    schema=schema,
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)],
                    schema=schema,
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=min_version,
            firefox_max_version=max_version,
            feature_configs=[feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature,
        )
        feature_value.value = json.dumps({"enabled": 1})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {
                    "feature_values": [
                        {
                            "value": [
                                "1 is not of type 'boolean' at version "
                                f"{major}.{minor}.{patch}"
                                for (major, minor, patch) in expected_versions
                            ]
                        }
                    ]
                }
            },
        )

    def test_validate_feature_versioned_before_versioned_range_valid(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(
                    version=None,
                    schema=json.dumps(
                        {
                            "type": "object",
                            "properties": {"kind": {"const": "unversioned"}},
                            "additionalProperties": False,
                        }
                    ),
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)],
                    schema=json.dumps(
                        {
                            "type": "object",
                            "properties": {"kind": {"const": "versioned"}},
                            "additionalProperties": False,
                        }
                    ),
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_110,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_111,
            feature_configs=[feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature
        )
        feature_value.value = json.dumps({"kind": "unversioned"})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    @parameterized.expand(
        [
            (
                NimbusExperiment.Version.FIREFOX_120,
                NimbusExperiment.Version.FIREFOX_120,
                ["120.0.0"],
            ),
            (
                NimbusExperiment.Version.FIREFOX_121,
                NimbusExperiment.Version.FIREFOX_121,
                ["121.0.0"],
            ),
            (
                NimbusExperiment.Version.FIREFOX_122,
                NimbusExperiment.Version.FIREFOX_122,
                ["122.0.0"],
            ),
            (
                NimbusExperiment.Version.FIREFOX_120,
                NimbusExperiment.Version.FIREFOX_121,
                ["121.0.0", "120.0.0"],
            ),
            (
                NimbusExperiment.Version.FIREFOX_120,
                NimbusExperiment.Version.NO_VERSION,
                ["122.0.0", "121.0.0", "120.0.0"],
            ),
            (
                NimbusExperiment.Version.FIREFOX_121,
                NimbusExperiment.Version.NO_VERSION,
                ["122.0.0", "121.0.0"],
            ),
            (
                NimbusExperiment.Version.FIREFOX_122,
                NimbusExperiment.Version.NO_VERSION,
                ["122.0.0"],
            ),
        ]
    )
    def test_validate_feature_versioned_schema_errors(
        self, min_version, max_version, error_versions
    ):
        json_schema = json.dumps(
            {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                    },
                },
                "additionalProperties": False,
            }
        )

        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)], schema=json_schema
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(121, 0, 0)], schema=json_schema
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)], schema=json_schema
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=min_version,
            firefox_max_version=max_version,
            feature_configs=[feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature
        )
        feature_value.value = json.dumps({"enabled": 1})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {
                    "feature_values": [
                        {
                            "value": [
                                f"1 is not of type 'boolean' at version {error_version}"
                                for error_version in error_versions
                            ],
                        }
                    ]
                }
            },
        )

    def test_validate_feature_versioned_localized_schema_errors(self):
        json_schema = json.dumps(
            {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                    },
                },
                "additionalProperties": False,
            }
        )

        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)], schema=json_schema
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(121, 0, 0)], schema=json_schema
                ),
            ],
        )

        locale_en_us = LocaleFactory.create(code="en-US")
        locale_en_ca = LocaleFactory.create(code="en-CA")

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_122,
            feature_configs=[feature],
            locales=[locale_en_us, locale_en_ca],
            is_localized=True,
            localizations=json.dumps(
                {
                    "en-US": {"enabled-value": "true"},
                    "en-CA": {"enabled-value": "true"},
                }
            ),
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature
        )
        feature_value.value = json.dumps(
            {
                "enabled": {
                    "$l10n": {
                        "id": "enabled-value",
                        "text": "enabled",
                        "comment": "comment",
                    },
                }
            }
        )
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
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
                                    "substitution for locale en-US at version 121.0.0"
                                ),
                                "'true' is not of type 'boolean' at version 121.0.0",
                                (
                                    "Schema validation errors occured during locale "
                                    "substitution for locale en-US at version 120.0.0"
                                ),
                                "'true' is not of type 'boolean' at version 120.0.0",
                                (
                                    "Schema validation errors occured during locale "
                                    "substitution for locale en-CA at version 121.0.0"
                                ),
                                "'true' is not of type 'boolean' at version 121.0.0",
                                (
                                    "Schema validation errors occured during locale "
                                    "substitution for locale en-CA at version 120.0.0"
                                ),
                                "'true' is not of type 'boolean' at version 120.0.0",
                            ]
                        }
                    ]
                }
            },
        )

    @parameterized.expand(
        [
            (
                NimbusExperiment.Version.FIREFOX_120,
                NimbusExperiment.Version.NO_VERSION,
                NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_VERSIONS.format(
                    feature_config="FEATURE",
                    versions="121.0.0",
                ),
            ),
            (
                NimbusExperiment.Version.FIREFOX_121,
                NimbusExperiment.Version.FIREFOX_121,
                NimbusConstants.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_RANGE.format(
                    feature_config="FEATURE",
                ),
            ),
        ]
    )
    def test_fml_validate_feature_versioned_unsupported_versions_error(
        self,
        min_version,
        max_version,
        expected_error,
    ):
        application = NimbusExperiment.Application.FENIX

        feature = NimbusFeatureConfigFactory.create(
            application=application,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)], schema=None
                ),
            ],
        )

        NimbusFeatureConfigFactory.create(
            application=application,
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(121, 0, 0)], schema=None
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)], schema=None
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            firefox_min_version=min_version,
            firefox_max_version=max_version,
            feature_configs=[feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertTrue(
            serializer.errors["reference_branch"]["feature_values"][0]["value"][
                0
            ].startswith(expected_error),
            serializer.errors,
        )

    def test_fml_validate_feature_versioned_truncated_range_fml_error(self):
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
        application = NimbusExperiment.Application.IOS
        min_version = NimbusExperiment.Version.FIREFOX_110
        max_version = NimbusExperiment.Version.NO_VERSION

        schema = json.dumps(
            {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                    },
                },
                "additionalProperties": False,
            }
        )

        feature = NimbusFeatureConfigFactory.create(
            application=application,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)],
                    schema=schema,
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(121, 0, 0)],
                    schema=schema,
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(122, 0, 0)],
                    schema=schema,
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            firefox_min_version=min_version,
            firefox_max_version=max_version,
            feature_configs=[feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature,
        )
        feature_value.value = json.dumps({"enabled": 1})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "reference_branch": {
                    "feature_values": [
                        {"value": ["In versions 120.0.0-122.0.0: Incorrect value!"]}
                    ]
                }
            },
            serializer.errors,
        )

    def test_fml_validate_feature_versioned_before_versioned_range_valid(self):
        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.FENIX,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(
                    version=None,
                    schema=json.dumps(
                        {
                            "type": "object",
                            "properties": {"kind": {"const": "unversioned"}},
                            "additionalProperties": False,
                        }
                    ),
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[(120, 0, 0)],
                    schema=json.dumps(
                        {
                            "type": "object",
                            "properties": {"kind": {"const": "versioned"}},
                            "additionalProperties": False,
                        }
                    ),
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_110,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_111,
            feature_configs=[feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature
        )
        feature_value.value = json.dumps({"kind": "unversioned"})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_fml_validate_feature_versioned_fml_error(self):
        fml_errors = [
            NimbusFmlErrorDataClass(
                line=2,
                col=0,
                message="Incorrect value",
                highlight="enabled",
            ),
            NimbusFmlErrorDataClass(
                line=0,
                col=1,
                message="Incorrect value again",
                highlight="enabled",
            ),
        ]
        self.setup_get_fml_errors(fml_errors)

        versions = [(120, 0, 0), (121, 0, 0)]

        schema = json.dumps(
            {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                    },
                },
                "additionalProperties": False,
            }
        )

        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.FENIX,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[versions[0]], schema=schema
                ),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[versions[1]], schema=schema
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_122,
            feature_configs=[feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature
        )
        feature_value.value = json.dumps({"enabled": 123})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            set(serializer.errors["reference_branch"]["feature_values"][0]["value"]),
            {
                "In versions 120.0.0-121.0.0: Incorrect value",
                "In versions 120.0.0-121.0.0: Incorrect value again",
            },
            serializer.errors,
        )

    def test_fml_validate_feature_versioned_range_treatment_branch_fml_errors(self):
        fml_errors = [
            NimbusFmlErrorDataClass(
                line=2,
                col=10,
                message="Incorrect value in the treatment branch!",
                highlight="disabled",
            ),
        ]
        self.setup_get_fml_errors(fml_errors)

        versions = [(120, 0, 0)]
        feature = "FEATURE"
        expected_errors = [
            NimbusExperiment.ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_RANGE.format(
                feature_config=feature,
            )
        ]

        schema = json.dumps(
            {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                    },
                },
                "additionalProperties": False,
            }
        )

        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.FENIX,
            slug="FEATURE",
            name=feature,
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
                NimbusVersionedSchemaFactory.build(
                    version=self.versions[versions[0]], schema=schema
                ),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_121,
            firefox_max_version=NimbusExperiment.Version.FIREFOX_121,
            feature_configs=[feature],
        )

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = json.dumps({"bang": {"bong": "boom"}})
        treatment_feature_value.save()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature
        )
        feature_value.value = json.dumps({"enabled": 123})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            expected_errors[0],
            serializer.errors["treatment_branches"][0]["feature_values"][0]["value"][0],
        )

    def test_fml_validate_feature_versioned_unbounded_range_valid(self):
        self.setup_fml_no_errors()

        feature = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.FENIX,
            slug="FEATURE",
            name="FEATURE",
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
            firefox_max_version=NimbusExperiment.Version.NO_VERSION,
            feature_configs=[feature],
        )

        for branch in experiment.treatment_branches:
            branch.delete()

        feature_value = experiment.reference_branch.feature_values.get(
            feature_config=feature
        )
        feature_value.value = json.dumps({"enabled": 123})
        feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(experiment, context={"user": self.user}).data,
            context={"user": self.user},
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.errors, {})


class TestNimbusReviewSerializerMultiFeature(MockFmlErrorMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.feature_without_schema = NimbusFeatureConfigFactory.create(
            slug="feature_without_schema",
            application=NimbusExperiment.Application.DESKTOP,
            schemas=[
                NimbusVersionedSchemaFactory.build(
                    version=None,
                    schema=None,
                )
            ],
        )
        self.feature_with_schema = NimbusFeatureConfigFactory.create(
            slug="feature_with_schema",
            application=NimbusExperiment.Application.DESKTOP,
            schemas=[
                NimbusVersionedSchemaFactory.build(
                    version=None,
                    schema=BASIC_JSON_SCHEMA,
                )
            ],
        )
        self.setup_fml_no_errors()

    def test_feature_configs_application_mismatches_error(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.RELEASE,
            feature_configs=[
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.FENIX,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=None,
                        )
                    ],
                ),
                NimbusFeatureConfigFactory.create(
                    application=NimbusExperiment.Application.IOS,
                    schemas=[
                        NimbusVersionedSchemaFactory.build(
                            version=None,
                            schema=None,
                        )
                    ],
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

    def test_feature_configs_value_schema_warn(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            status=NimbusExperiment.Status.DRAFT,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
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
            {"directMigrateSingleProfile": true, "DDirectMigrateSingleProfile": true}
        """.strip()
        reference_feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get(
            feature_config=self.feature_with_schema
        )
        treatment_feature_value.value = """\
            {"directMigrateSingleProfile": true, "DDirectMigrateSingleProfile": true}
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
        ) >= NimbusExperiment.Version.parse(
            NimbusExperiment.MIN_REQUIRED_VERSION
        ) or NimbusExperiment.Application.is_web(application)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            firefox_min_version=firefox_min_version,
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
        feature = NimbusFeatureConfigFactory.create(
            application=application,
            schemas=[
                NimbusVersionedSchemaFactory.build(
                    version=None,
                    schema=None,
                )
            ],
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
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

    @parameterized.expand(
        [
            (20, True),
            (21, False),
        ]
    )
    def test_multifeature_max_features(self, feature_count, expected_valid):
        application = NimbusExperiment.Application.DESKTOP
        features = [
            NimbusFeatureConfigFactory(application=application)
            for _ in range(feature_count)
        ]

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=features,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
        )

        for fv in experiment.reference_branch.feature_values.all():
            fv.value = "{}"
            fv.save()

        experiment.branches.exclude(id=experiment.reference_branch.id).delete()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )

        if expected_valid:
            self.assertTrue(serializer.is_valid(), serializer.errors)
        else:
            self.assertFalse(serializer.is_valid())
            self.assertEqual(
                serializer.errors,
                {
                    "feature_configs": [
                        NimbusExperiment.ERROR_MULTIFEATURE_TOO_MANY_FEATURES
                    ]
                },
            )

    @parameterized.expand(
        [
            ({"feature-1": "bogus-collection"},),
            (
                {
                    "feature-1": "bogus-collection",
                    "feature-2": "bogus-collection",
                },
            ),
        ]
    )
    def test_validate_feature_configs_alternate_collection(
        self, kinto_collections_by_feature_id
    ):
        with patch.object(
            experimenter.experiments.constants.APPLICATION_CONFIG_DESKTOP,
            "kinto_collections_by_feature_id",
            kinto_collections_by_feature_id,
        ):
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.CREATED,
                firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
                feature_configs=[
                    NimbusFeatureConfigFactory.create(
                        name="feature-1",
                        slug="feature-1",
                        application=NimbusExperiment.Application.DESKTOP,
                    ),
                ],
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

    @parameterized.expand(
        [
            ({"feature-1": "collection-1"},),
            ({"feature-1": "collection-1", "feature-2": "collection-2"},),
        ]
    )
    def test_validate_feature_configs_multiple_alternate_collections(
        self, kinto_collections_by_feature_id
    ):
        default_collection = experimenter.experiments.constants.APPLICATION_CONFIG_DESKTOP.default_kinto_collection  # noqa: E501

        with patch.object(
            experimenter.experiments.constants.APPLICATION_CONFIG_DESKTOP,
            "kinto_collections_by_feature_id",
            kinto_collections_by_feature_id,
        ):
            experiment = NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.CREATED,
                firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
                feature_configs=[
                    NimbusFeatureConfigFactory.create(
                        name=slug,
                        slug=slug,
                        application=NimbusExperiment.Application.DESKTOP,
                    )
                    for slug in ("feature-1", "feature-2")
                ],
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
                serializer.errors,
                {
                    "feature_configs": [
                        NimbusConstants.ERROR_INCOMPATIBLE_FEATURES,
                        NimbusConstants.ERROR_FEATURE_TARGET_COLLECTION.format(
                            feature_id="feature-1",
                            collection="collection-1",
                        ),
                        NimbusConstants.ERROR_FEATURE_TARGET_COLLECTION.format(
                            feature_id="feature-2",
                            collection=kinto_collections_by_feature_id.get(
                                "feature-2", default_collection
                            ),
                        ),
                    ]
                },
            )

    def test_feature_values_with_different_variables_is_invalid(self):
        application = NimbusExperiment.Application.DESKTOP
        feature = NimbusFeatureConfigFactory.create(
            application=application,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            warn_feature_schema=False,
        )
        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps({"a": "x", "b": "y"})
        feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = json.dumps({"b": "y", "c": "z"})
        treatment_feature_value.save()

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
            NimbusConstants.ERROR_FEATURE_VALUE_DIFFERENT_VARIABLES.format(variables="c"),
            serializer.errors["reference_branch"]["feature_values"][0]["value"],
        )
        self.assertIn(
            NimbusConstants.ERROR_FEATURE_VALUE_DIFFERENT_VARIABLES.format(variables="a"),
            serializer.errors["treatment_branches"][0]["feature_values"][0]["value"],
        )

    def test_feature_values_with_different_variables_external_schema_is_valid(self):
        application = NimbusExperiment.Application.DESKTOP
        feature = NimbusFeatureConfigFactory.create(
            application=application,
        )
        feature.schemas.update(has_remote_schema=True)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            warn_feature_schema=False,
        )
        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps({"a": "x", "b": "y"})
        feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = json.dumps({"b": "y", "c": "z"})
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )

        self.assertTrue(serializer.is_valid())

    def test_feature_values_with_different_variables_warns(self):
        application = NimbusExperiment.Application.DESKTOP
        feature = NimbusFeatureConfigFactory.create(
            application=application,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            warn_feature_schema=True,
        )
        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = json.dumps({"a": "x", "b": "y"})
        feature_value.save()

        treatment_feature_value = experiment.treatment_branches[0].feature_values.get()
        treatment_feature_value.value = json.dumps({"b": "y", "c": "z"})
        treatment_feature_value.save()

        serializer = NimbusReviewSerializer(
            experiment,
            data=NimbusReviewSerializer(
                experiment,
                context={"user": self.user},
            ).data,
            context={"user": self.user},
            partial=True,
        )

        self.assertTrue(serializer.is_valid())
        self.assertIn(
            NimbusConstants.ERROR_FEATURE_VALUE_DIFFERENT_VARIABLES.format(variables="c"),
            serializer.warnings["reference_branch"]["feature_values"][0]["value"],
        )
        self.assertIn(
            NimbusConstants.ERROR_FEATURE_VALUE_DIFFERENT_VARIABLES.format(variables="a"),
            serializer.warnings["treatment_branches"][0]["feature_values"][0]["value"],
        )

    def test_primary_secondary_outcome_intersection_is_invalid(self):
        application = NimbusExperiment.Application.DESKTOP
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            primary_outcomes=["outcome"],
            secondary_outcomes=["outcome"],
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
        self.assertIn(
            NimbusExperiment.ERROR_PRIMARY_SECONDARY_OUTCOMES_INTERSECTION,
            serializer.errors["primary_outcomes"],
        )
        self.assertIn(
            NimbusExperiment.ERROR_PRIMARY_SECONDARY_OUTCOMES_INTERSECTION,
            serializer.errors["secondary_outcomes"],
        )
