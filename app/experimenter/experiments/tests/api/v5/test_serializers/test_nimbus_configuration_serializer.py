from django.test import TestCase

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.api.v5.serializers import (
    NimbusConfigurationDataClass,
    NimbusConfigurationSerializer,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.outcomes import Outcomes


class TestNimbusConfigurationSerializer(TestCase):
    def test_expected_output(self):
        feature_configs = NimbusFeatureConfigFactory.create_batch(10)
        experiment = NimbusExperimentFactory.create()

        config = NimbusConfigurationSerializer(NimbusConfigurationDataClass()).data

        def assertChoices(data, text_choices):
            self.assertEqual(len(data), len(text_choices.names))
            for index, name in enumerate(text_choices.names):
                self.assertEqual(data[index]["label"], text_choices[name].label)
                self.assertEqual(data[index]["value"], name)

        assertChoices(config["applications"], NimbusExperiment.Application)
        assertChoices(config["channels"], NimbusExperiment.Channel)
        assertChoices(
            config["conclusionRecommendations"], NimbusExperiment.ConclusionRecommendation
        )
        assertChoices(config["firefoxVersions"], NimbusExperiment.Version)
        assertChoices(config["documentationLink"], NimbusExperiment.DocumentationLink)
        self.assertEqual(len(config["allFeatureConfigs"]), 18)

        for application_config_data in config["applicationConfigs"]:
            application_config = NimbusExperiment.APPLICATION_CONFIGS[
                NimbusExperiment.Application[application_config_data["application"]]
            ]
            channels = [
                channel["value"] for channel in application_config_data["channels"]
            ]
            self.assertEqual(
                set(channels),
                set(
                    [channel.name for channel in application_config.channel_app_id.keys()]
                ),
            )

        self.assertEqual(config["owners"], [{"username": experiment.owner.username}])

        for outcome in Outcomes.all():
            self.assertIn(
                {
                    "slug": outcome.slug,
                    "friendlyName": outcome.friendly_name,
                    "application": NimbusExperiment.Application(outcome.application).name,
                    "description": outcome.description,
                    "isDefault": outcome.is_default,
                    "metrics": [
                        {
                            "slug": metric.slug,
                            "friendlyName": metric.friendly_name,
                            "description": metric.description,
                        }
                        for metric in outcome.metrics
                    ],
                },
                config["outcomes"],
            )

        for feature_config in feature_configs:
            self.assertIn(
                {
                    "id": feature_config.id,
                    "name": feature_config.name,
                    "slug": feature_config.slug,
                    "description": feature_config.description,
                    "application": NimbusExperiment.Application(
                        feature_config.application
                    ).name,
                    "ownerEmail": feature_config.owner_email,
                    "schema": feature_config.schema,
                },
                config["allFeatureConfigs"],
            )

        for targeting_config_choice in NimbusExperiment.TargetingConfig:
            targeting_config = NimbusExperiment.TARGETING_CONFIGS[
                targeting_config_choice.value
            ]
            self.assertIn(
                {
                    "label": targeting_config_choice.label,
                    "value": targeting_config_choice.value,
                    "description": targeting_config.description,
                    "stickyRequired": targeting_config.sticky_required,
                    "applicationValues": list(targeting_config.application_choice_names),
                    "isFirstRunRequired": targeting_config.is_first_run_required,
                },
                config["targetingConfigs"],
            )

        self.assertEqual(config["hypothesisDefault"], NimbusExperiment.HYPOTHESIS_DEFAULT)
        self.assertEqual(
            config["maxPrimaryOutcomes"], NimbusExperiment.MAX_PRIMARY_OUTCOMES
        )

        for locale in Locale.objects.all():
            self.assertIn({"code": locale.code, "name": locale.name}, config["locales"])

        for country in Country.objects.all():
            self.assertIn(
                {"code": country.code, "name": country.name}, config["countries"]
            )

        for language in Language.objects.all():
            self.assertIn(
                {"code": language.code, "name": language.name}, config["languages"]
            )
