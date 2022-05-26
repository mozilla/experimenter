import json

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.api.v2.serializers import (
    ExperimentCSVSerializer,
    ExperimentDesignAddonSerializer,
    ExperimentDesignGenericSerializer,
    ExperimentDesignMessageSerializer,
    ExperimentDesignMultiPrefSerializer,
    ExperimentDesignPrefSerializer,
    ExperimentTimelinePopSerializer,
)
from experimenter.experiments.api.v2.views import ExperimentCSVRenderer
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
    VariantPreferencesFactory,
)
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.openidc.tests.factories import UserFactory
from experimenter.projects.tests.factories import ProjectFactory


class TestExperimentSendIntentToShipEmailView(TestCase):
    def test_put_to_view_sends_email(self):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create_with_variants(
            review_intent_to_ship=False, status=Experiment.STATUS_REVIEW
        )
        old_outbox_len = len(mail.outbox)

        response = self.client.put(
            reverse(
                "experiments-api-send-intent-to-ship-email",
                kwargs={"slug": experiment.slug},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        experiment = Experiment.objects.get(pk=experiment.pk)
        self.assertEqual(experiment.review_intent_to_ship, True)
        self.assertEqual(len(mail.outbox), old_outbox_len + 1)

    def test_put_raises_409_if_email_already_sent(self):
        experiment = ExperimentFactory.create_with_variants(
            review_intent_to_ship=True, status=Experiment.STATUS_REVIEW
        )

        response = self.client.put(
            reverse(
                "experiments-api-send-intent-to-ship-email",
                kwargs={"slug": experiment.slug},
            ),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )

        self.assertEqual(response.status_code, 409)


class TestExperimentCloneView(TestCase):
    def test_patch_to_view_returns_clone_name_and_url(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        user_email = "user@example.com"

        data = json.dumps({"name": "best experiment"})

        response = self.client.patch(
            reverse("experiments-api-clone", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "best experiment")
        self.assertEqual(response.json()["clone_url"], "/experiments/best-experiment/")


class TestExperimentDesignPrefView(TestCase):
    def test_get_design_pref_returns_design_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants(type="pref")

        response = self.client.get(
            reverse("experiments-design-pref", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentDesignPrefSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_saves_design_info(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
            "value": "value 1",
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
            "value": "value 2",
        }

        data = json.dumps(
            {
                "type": "pref",
                "is_multi_pref": False,
                "pref_name": "pref 1",
                "pref_branch": "default",
                "pref_type": "string",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-pref", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_returns_400_on_missing_required_field(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
            "value": "value 1",
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
            "value": "value 2",
        }

        data = json.dumps(
            {
                "type": "pref",
                "pref_branch": "default",
                "pref_type": "string",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-pref", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["pref_name"], ["This field is required."])


class TestExperimentDesignMultiPrefView(TestCase):
    def setUp(self):
        self.user_email = "user@example.com"
        self.experiment = ExperimentFactory.create(type="pref")
        self.variant = ExperimentVariantFactory.create(
            experiment=self.experiment, is_control=True
        )
        self.preference = VariantPreferencesFactory.create(variant=self.variant)

    def test_get_design_multi_pref_returns_design_info(self):

        response = self.client.get(
            reverse(
                "experiments-design-multi-pref", kwargs={"slug": self.experiment.slug}
            ),
            **{settings.OPENIDC_EMAIL_HEADER: self.user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        serialized_experiment = ExperimentDesignMultiPrefSerializer(self.experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_save_design_info(self):
        experiment = ExperimentFactory.create(
            name="an experiment", slug="an-experiment", type="pref"
        )
        variant = {
            "name": "variant1",
            "ratio": 100,
            "description": "variant1 description",
            "is_control": True,
            "preferences": [
                {
                    "pref_name": "the name is pref name",
                    "pref_value": "it's a string value",
                    "pref_type": "string",
                    "pref_branch": "default",
                }
            ],
        }
        data = json.dumps(
            {"type": Experiment.TYPE_PREF, "is_multi_pref": True, "variants": [variant]}
        )

        response = self.client.put(
            reverse("experiments-design-multi-pref", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: self.user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_returns_400_for_dup_pref_name(self):
        experiment = ExperimentFactory.create(
            name="an experiment", slug="an-experiment", type="pref"
        )
        variant = {
            "name": "variant1",
            "ratio": 100,
            "description": "variant1 description",
            "is_control": True,
            "preferences": [
                {
                    "pref_name": "the name is pref name",
                    "pref_value": "it's a string value",
                    "pref_type": "string",
                    "pref_branch": "default",
                },
                {
                    "pref_name": "the name is pref name",
                    "pref_value": "it's another string value",
                    "pref_type": "string",
                    "pref_branch": "default",
                },
            ],
        }
        data = json.dumps({"variants": [variant]})

        response = self.client.put(
            reverse("experiments-design-multi-pref", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: self.user_email},
        )

        self.assertEqual(response.status_code, 400)


class TestExperimentDesignAddonView(TestCase):
    def test_get_design_addon_returns_design_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_ADDON
        )

        response = self.client.get(
            reverse("experiments-design-addon", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)

        serialized_experiment = ExperimentDesignAddonSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_saves_design_info(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_ADDON,
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = json.dumps(
            {
                "type": ExperimentConstants.TYPE_ADDON,
                "addon_experiment_id": "1234",
                "is_branched_addon": False,
                "addon_release_url": "http://www.example.com",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-addon", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_returns_400_on_missing_required_field(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_ADDON,
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = json.dumps(
            {
                "type": ExperimentConstants.TYPE_ADDON,
                "addon_experiment_id": "1234",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-addon", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["addon_release_url"], ["This field is required."]
        )


class TestExperimentDesignGenericView(TestCase):
    def test_get_returns_design_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_GENERIC
        )

        response = self.client.get(
            reverse("experiments-design-generic", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)

        serialized_experiment = ExperimentDesignGenericSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_saves_design_info(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_GENERIC,
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = json.dumps(
            {
                "type": ExperimentConstants.TYPE_GENERIC,
                "design": "design 1",
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-generic", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_design_is_optional(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_GENERIC,
        )
        user_email = "user@example.com"

        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = json.dumps(
            {"type": ExperimentConstants.TYPE_GENERIC, "variants": [variant_1, variant_2]}
        )

        response = self.client.put(
            reverse("experiments-design-generic", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)


class TestExperimentDesignMessageView(TestCase):
    def test_get_returns_design_info(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_MESSAGE
        )

        response = self.client.get(
            reverse("experiments-design-message", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)

        serialized_experiment = ExperimentDesignMessageSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_saves_cfr_info(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_MESSAGE,
        )
        user_email = "user@example.com"

        variant_1 = {
            "is_control": True,
            "ratio": 50,
            "name": "control name",
            "description": "control description",
            "message_targeting": "control targeting",
            "message_threshold": "control threshold",
            "message_triggers": "control triggers",
            "value": "control content",
        }

        variant_2 = {
            "is_control": False,
            "ratio": 50,
            "name": "treatment name",
            "description": "treatment description",
            "message_targeting": "treatment targeting",
            "message_threshold": "treatment threshold",
            "message_triggers": "treatment triggers",
            "value": "treatment content",
        }

        data = json.dumps(
            {
                "message_type": Experiment.MESSAGE_TYPE_CFR,
                "message_template": Experiment.MESSAGE_TEMPLATE_DOOR,
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-message", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

    def test_put_to_view_saves_about_welcome_info(self):
        experiment = ExperimentFactory.create(
            name="great experiment",
            slug="great-experiment",
            type=ExperimentConstants.TYPE_MESSAGE,
        )
        user_email = "user@example.com"
        variant_1 = {
            "is_control": True,
            "ratio": 50,
            "name": "control name",
            "description": "control description",
            "value": "control content",
        }

        variant_2 = {
            "is_control": False,
            "ratio": 50,
            "name": "treatment name",
            "description": "treatment description",
            "value": "treatment content",
        }

        data = json.dumps(
            {
                "message_type": Experiment.MESSAGE_TYPE_WELCOME,
                "variants": [variant_1, variant_2],
            }
        )

        response = self.client.put(
            reverse("experiments-design-message", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)


class TestExperimentTimelinePopulationView(TestCase):
    def test_get_timeline_pop_returns_info(self):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        response = self.client.get(
            reverse("experiments-timeline-population", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        json_data = json.loads(response.content)

        serialized_experiment = ExperimentTimelinePopSerializer(experiment).data
        self.assertEqual(serialized_experiment, json_data)

    def test_put_to_view_timeline_pop_info(self):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        data = json.dumps(
            {
                "client_matching": "client match info",
                "firefox_min_version": "67.0",
                "countries": [],
                "locales": [],
            }
        )

        response = self.client.put(
            reverse("experiments-timeline-population", kwargs={"slug": experiment.slug}),
            data,
            content_type="application/json",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)


class TestExperimentCSVListView(TestCase):
    def test_get_returns_csv_info(self):
        user_email = "user@example.com"
        experiment1 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="a"
        )
        experiment2 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="b"
        )

        response = self.client.get(
            reverse("experiments-api-csv"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = ExperimentCSVRenderer().render(
            ExperimentCSVSerializer([experiment1, experiment2], many=True).data,
            renderer_context={"header": ExperimentCSVSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)

    def test_view_filters_by_project(self):
        user_email = "user@example.com"
        project = ProjectFactory.create()
        experiment1 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="a", projects=[project]
        )
        experiment2 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="b", projects=[project]
        )
        ExperimentFactory.create_with_variants()

        url = reverse("experiments-api-csv")
        response = self.client.get(
            f"{url}?projects={project.id}", **{settings.OPENIDC_EMAIL_HEADER: user_email}
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = ExperimentCSVRenderer().render(
            ExperimentCSVSerializer([experiment1, experiment2], many=True).data,
            renderer_context={"header": ExperimentCSVSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)

    def test_view_filters_by_subscriber(self):
        user = UserFactory(email="user@example.com")
        experiment1 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="a"
        )
        experiment1.subscribers.add(user)
        experiment2 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="b"
        )
        experiment2.subscribers.add(user)
        ExperimentFactory.create_with_variants()

        url = reverse("experiments-api-csv")
        response = self.client.get(
            f"{url}?subscribed=on", **{settings.OPENIDC_EMAIL_HEADER: user.email}
        )

        self.assertEqual(response.status_code, 200)

        csv_data = response.content
        expected_csv_data = ExperimentCSVRenderer().render(
            ExperimentCSVSerializer([experiment1, experiment2], many=True).data,
            renderer_context={"header": ExperimentCSVSerializer.Meta.fields},
        )
        self.assertEqual(csv_data, expected_csv_data)
