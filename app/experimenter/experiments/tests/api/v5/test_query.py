import json

from django.conf import settings
from django.urls import reverse
from graphene.utils.str_converters import to_snake_case
from graphene_django.utils.testing import GraphQLTestCase

from experimenter.experiments.models.nimbus import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.experiments.tests.factories.nimbus import (
    NimbusFeatureConfigFactory,
    NimbusProbeSetFactory,
)


class TestNimbusQuery(GraphQLTestCase):
    GRAPHQL_URL = reverse("nimbus-api-graphql")

    def test_experiments(self):
        user_email = "user@example.com"
        exp = NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.DRAFT)

        response = self.query(
            """
            query {
                experiments {
                    name
                    slug
                    publicDescription
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiments = content["data"]["experiments"]
        self.assertEqual(len(experiments), 1)
        for key in experiments[0]:
            self.assertEqual(experiments[0][key], str(getattr(exp, to_snake_case(key))))

    def test_experiments_by_status(self):
        user_email = "user@example.com"
        draft_exp = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )
        NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.ACCEPTED)

        response = self.query(
            """
            query {
                experiments(status: Draft) {
                    name
                    slug
                    publicDescription
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiments = content["data"]["experiments"]
        self.assertEqual(len(experiments), 1)
        for key in experiments[0]:
            self.assertEqual(
                experiments[0][key], str(getattr(draft_exp, to_snake_case(key)))
            )

    def test_experiment_by_slug_ready_for_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    name
                    slug
                    publicDescription
                    readyForReview {
                        message
                        ready
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(experiment_data["name"], experiment.name)
        self.assertEqual(experiment_data["slug"], experiment.slug)
        self.assertEqual(
            experiment_data["publicDescription"], experiment.public_description
        )
        self.assertEqual(
            experiment_data["readyForReview"], {"message": {}, "ready": True}
        )

    def test_experiment_by_slug_not_ready_for_review(self):
        user_email = "user@example.com"
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT, hypothesis=NimbusExperiment.HYPOTHESIS_DEFAULT
        )

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    readyForReview {
                        message
                        ready
                    }
                }
            }
            """,
            variables={"slug": experiment.slug},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200, response.content)
        content = json.loads(response.content)
        experiment_data = content["data"]["experimentBySlug"]
        self.assertEqual(
            experiment_data["readyForReview"],
            {
                "message": {"hypothesis": ["Hypothesis cannot be the default value."]},
                "ready": False,
            },
        )

    def test_experiment_by_slug_not_found(self):
        user_email = "user@example.com"
        NimbusExperimentFactory.create_with_status(NimbusExperiment.Status.DRAFT)

        response = self.query(
            """
            query experimentBySlug($slug: String!) {
                experimentBySlug(slug: $slug) {
                    name
                    slug
                    publicDescription
                }
            }
            """,
            variables={"slug": "nope"},
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        experiment = content["data"]["experimentBySlug"]
        self.assertIsNone(experiment)

    def test_nimbus_config(self):
        user_email = "user@example.com"
        # Create some probes and feature configs
        feature_configs = NimbusFeatureConfigFactory.create_batch(10)
        probe_sets = NimbusProbeSetFactory.create_batch(10)

        response = self.query(
            """
            query{
                nimbusConfig{
                    applicationChannels {
                        label
                        channels
                    }
                    application {
                        label
                        value
                    }
                    channels {
                        label
                        value
                    }
                    firefoxMinVersion {
                        label
                        value
                    }
                    featureConfig {
                        name
                        slug
                        id
                        description
                    }
                    probeSets {
                        id
                        name
                    }
                    targetingConfigSlug {
                        label
                        value
                    }
                    hypothesisDefault
                    maxPrimaryProbeSets
                }
            }
            """,
            headers={settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        config = content["data"]["nimbusConfig"]

        def assertChoices(data, text_choices):
            self.assertEqual(len(data), len(text_choices.names))
            for index, name in enumerate(text_choices.names):
                self.assertEqual(data[index]["label"], text_choices[name].label)
                self.assertEqual(data[index]["value"], name)

        assertChoices(config["application"], NimbusExperiment.Application)
        assertChoices(config["channels"], NimbusExperiment.Channel)
        assertChoices(config["firefoxMinVersion"], NimbusExperiment.Version)
        assertChoices(config["targetingConfigSlug"], NimbusExperiment.TargetingConfig)
        self.assertEqual(len(config["featureConfig"]), 10)
        self.assertEqual(len(config["probeSets"]), 10)
        app_channels = config["applicationChannels"]
        self.assertEqual(len(app_channels), len(NimbusExperiment.ApplicationChannels))
        # Transform list to dict for easier comparison
        app_channel_dict = {ac["label"]: ac["channels"] for ac in app_channels}
        for app_label, channel_names in NimbusExperiment.ApplicationChannels.items():
            app_compare_channels = app_channel_dict[app_label.label]
            self.assertEqual(
                set(app_compare_channels),
                set(channel.label for channel in channel_names),
            )
        for probe_set in probe_sets:
            config_probe_set = next(
                filter(lambda p: p["id"] == str(probe_set.id), config["probeSets"])
            )
            self.assertEqual(config_probe_set["id"], str(probe_set.id))
            self.assertEqual(config_probe_set["name"], probe_set.name)
        for feature_config in feature_configs:
            config_feature_config = next(
                filter(
                    lambda f: f["id"] == str(feature_config.id), config["featureConfig"]
                )
            )
            self.assertEqual(config_feature_config["id"], str(feature_config.id))
            self.assertEqual(config_feature_config["name"], feature_config.name)
            self.assertEqual(config_feature_config["slug"], feature_config.slug)
            self.assertEqual(
                config_feature_config["description"], feature_config.description
            )
        self.assertEqual(config["hypothesisDefault"], NimbusExperiment.HYPOTHESIS_DEFAULT)
        self.assertEqual(
            config["maxPrimaryProbeSets"], NimbusExperiment.MAX_PRIMARY_PROBE_SETS
        )
