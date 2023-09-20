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
    NimbusVersionedSchemaFactory,
)
from experimenter.jetstream.tests.mixins import MockSizingDataMixin
from experimenter.outcomes import Outcomes
from experimenter.projects.models import Project


class TestNimbusConfigurationSerializer(MockSizingDataMixin, TestCase):
    def test_expected_output(self):
        self.setup_cached_sizing_data()
        feature_configs = NimbusFeatureConfigFactory.create_batch(8)
        feature_configs.append(
            NimbusFeatureConfigFactory.create(
                schemas=[
                    NimbusVersionedSchemaFactory.build(
                        version=None,
                        sets_prefs=["foo.bar.baz"],
                    )
                ],
            ),
        )
        feature_configs.append(
            NimbusFeatureConfigFactory.create(
                schemas=[
                    NimbusVersionedSchemaFactory.build(
                        version=None,
                        sets_prefs=["qux.quux.corge", "grault.garply.waldo"],
                    )
                ]
            )
        )
        experiment = NimbusExperimentFactory.create()

        config = NimbusConfigurationSerializer(NimbusConfigurationDataClass()).data

        def assertChoices(data, text_choices):
            self.assertEqual(len(data), len(text_choices.names))
            for index, name in enumerate(text_choices.names):
                self.assertEqual(data[index]["label"], text_choices[name].label)
                self.assertEqual(data[index]["value"], name)

        assertChoices(config["applications"], NimbusExperiment.Application)
        assertChoices(config["channels"], NimbusExperiment.Channel)
        assertChoices(config["takeaways"], NimbusExperiment.Takeaways)
        assertChoices(config["types"], NimbusExperiment.Type)
        assertChoices(
            config["conclusionRecommendations"],
            NimbusExperiment.ConclusionRecommendation,
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
                {channel.name for channel in application_config.channel_app_id},
            )

        self.assertEqual(config["owners"], [{"username": experiment.owner.username}])

        pop_sizing_data = self.get_cached_sizing_data()
        self.assertEqual(
            config["populationSizingData"], pop_sizing_data.json(exclude_unset=True)
        )

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
                    "schema": feature_config.schemas.get(version=None).schema,
                    "setsPrefs": bool(
                        feature_config.schemas.get(version=None).sets_prefs
                    ),
                    "enabled": bool(feature_config.enabled),
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

        for project in Project.objects.all():
            self.assertIn(
                {"id": project.id, "name": project.name, "slug": project.slug},
                [dict(i) for i in config["projects"]],
            ),
