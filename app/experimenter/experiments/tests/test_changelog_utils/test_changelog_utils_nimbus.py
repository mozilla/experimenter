from django.test import TestCase

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.changelog_utils import (
    NimbusExperimentChangeLogSerializer,
    generate_nimbus_changelog,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.experiments.tests.factories.nimbus import (
    NimbusChangeLogFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes
from experimenter.projects.tests.factories import ProjectFactory


@mock_valid_outcomes
class TestNimbusExperimentChangeLogSerializer(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Outcomes.clear_cache()

    def test_outputs_expected_schema_for_empty_experiment(self):
        owner = UserFactory.create()
        experiment = NimbusExperiment.objects.create(owner=owner)
        data = dict(NimbusExperimentChangeLogSerializer(experiment).data)
        self.assertEqual(
            data,
            {
                "application": "",
                "branches": [],
                "channel": NimbusExperiment.Channel.NO_CHANNEL,
                "conclusion_recommendation": None,
                "countries": [],
                "feature_configs": [],
                "firefox_min_version": NimbusExperiment.Version.NO_VERSION,
                "firefox_max_version": NimbusExperiment.Version.NO_VERSION,
                "hypothesis": NimbusExperiment.HYPOTHESIS_DEFAULT,
                "is_rollout": experiment.is_rollout,
                "is_archived": experiment.is_archived,
                "is_paused": False,
                "locales": [],
                "languages": [],
                "name": "",
                "owner": owner.email,
                "parent": None,
                "population_percent": "0.0000",
                "primary_outcomes": [],
                "projects": [],
                "proposed_duration": NimbusExperiment.DEFAULT_PROPOSED_DURATION,
                "proposed_enrollment": NimbusExperiment.DEFAULT_PROPOSED_ENROLLMENT,
                "public_description": "",
                "publish_status": NimbusExperiment.PublishStatus.IDLE,
                "published_dto": None,
                "reference_branch": None,
                "results_data": None,
                "risk_brand": None,
                "risk_mitigation_link": "",
                "risk_partner_related": None,
                "risk_revenue": None,
                "secondary_outcomes": [],
                "slug": "",
                "status_next": None,
                "status": NimbusExperiment.Status.DRAFT,
                "takeaways_summary": None,
                "targeting_config_slug": NimbusExperiment.TargetingConfig.NO_TARGETING,
                "total_enrolled_clients": 0,
                "warn_feature_schema": False,
            },
        )

    def test_outputs_expected_schema_for_complete_experiment(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create()
        project = ProjectFactory.create()
        primary_outcome = Outcomes.by_application(application)[0].slug
        secondary_outcome = Outcomes.by_application(application)[1].slug
        parent_experiment = NimbusExperimentFactory.create()

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            feature_configs=[feature_config],
            projects=[project],
            primary_outcomes=[primary_outcome],
            secondary_outcomes=[secondary_outcome],
            parent=parent_experiment,
        )
        data = dict(NimbusExperimentChangeLogSerializer(experiment).data)
        branches_data = [dict(b) for b in data.pop("branches")]
        control_branch_data = dict(data.pop("reference_branch"))
        locales_data = data.pop("locales")
        countries_data = data.pop("countries")
        languages_data = data.pop("languages")
        feature_configs_data = data.pop("feature_configs")
        published_dto_data = data.pop("published_dto")

        self.assertEqual(
            data,
            {
                "application": experiment.application,
                "channel": experiment.channel,
                "conclusion_recommendation": None,
                "firefox_min_version": experiment.firefox_min_version,
                "firefox_max_version": experiment.firefox_max_version,
                "hypothesis": experiment.hypothesis,
                "is_rollout": experiment.is_rollout,
                "is_archived": experiment.is_archived,
                "is_paused": experiment.is_paused,
                "name": experiment.name,
                "owner": experiment.owner.email,
                "parent": parent_experiment.slug,
                "population_percent": str(experiment.population_percent),
                "primary_outcomes": [primary_outcome],
                "projects": [project.slug],
                "proposed_duration": experiment.proposed_duration,
                "proposed_enrollment": experiment.proposed_enrollment,
                "public_description": experiment.public_description,
                "publish_status": experiment.publish_status,
                "results_data": None,
                "risk_brand": experiment.risk_brand,
                "risk_mitigation_link": experiment.risk_mitigation_link,
                "risk_partner_related": experiment.risk_partner_related,
                "risk_revenue": experiment.risk_revenue,
                "secondary_outcomes": [secondary_outcome],
                "slug": experiment.slug,
                "status_next": experiment.status_next,
                "takeaways_summary": None,
                "status": experiment.status,
                "targeting_config_slug": experiment.targeting_config_slug,
                "total_enrolled_clients": experiment.total_enrolled_clients,
                "warn_feature_schema": False,
            },
        )

        self.assertEqual(
            published_dto_data.keys(),
            dict(NimbusExperimentSerializer(experiment).data).keys(),
        )

        for feature_config in experiment.feature_configs.all():
            self.assertIn(
                {
                    "application": feature_config.application,
                    "description": feature_config.description,
                    "name": feature_config.name,
                    "owner_email": feature_config.owner_email,
                    "read_only": feature_config.read_only,
                    "schema": feature_config.schema,
                    "slug": feature_config.slug,
                },
                feature_configs_data,
            )

        self.assertEqual(
            set(locales_data),
            set(experiment.locales.all().values_list("code", flat=True)),
        )

        self.assertEqual(
            set(countries_data),
            set(experiment.countries.all().values_list("code", flat=True)),
        )

        self.assertEqual(
            set(languages_data),
            set(experiment.languages.all().values_list("code", flat=True)),
        )

        self.assertEqual(
            control_branch_data,
            {
                "description": experiment.reference_branch.description,
                "name": experiment.reference_branch.name,
                "ratio": experiment.reference_branch.ratio,
                "slug": experiment.reference_branch.slug,
                "feature_values": [
                    {
                        "enabled": (
                            experiment.reference_branch.feature_values.get().enabled
                        ),
                        "value": experiment.reference_branch.feature_values.get().value,
                        "branch": experiment.reference_branch.id,
                        "feature_config": experiment.feature_configs.get().id,
                    }
                ],
            },
        )

        for branch in experiment.branches.all():
            self.assertIn(
                {
                    "description": branch.description,
                    "name": branch.name,
                    "ratio": branch.ratio,
                    "slug": branch.slug,
                    "feature_values": [
                        {
                            "enabled": branch.feature_values.get().enabled,
                            "value": branch.feature_values.get().value,
                            "branch": branch.id,
                            "feature_config": experiment.feature_configs.get().id,
                        }
                    ],
                },
                branches_data,
            )


class TestGenerateNimbusChangeLog(TestCase):
    maxDiff = None

    def setUp(self):
        self.user = UserFactory.create()

    def test_generate_nimbus_changelog_without_prior_change(self):
        experiment = NimbusExperimentFactory.create()

        self.assertEqual(experiment.changes.count(), 0)

        generate_nimbus_changelog(experiment, self.user, "test message")

        self.assertEqual(experiment.changes.count(), 1)

        change = experiment.changes.get()

        self.assertEqual(change.experiment, experiment)
        self.assertEqual(change.message, "test message")
        self.assertEqual(change.changed_by, self.user)
        self.assertEqual(change.old_status, None)
        self.assertEqual(change.old_status_next, None)
        self.assertEqual(change.old_publish_status, None)
        self.assertEqual(change.new_status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(change.new_status_next, None)
        self.assertEqual(change.new_publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertEqual(
            change.experiment_data,
            dict(NimbusExperimentChangeLogSerializer(experiment).data),
        )

    def test_generate_nimbus_changelog_with_prior_change(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        self.assertEqual(experiment.changes.count(), 1)

        experiment.status = NimbusExperiment.Status.DRAFT
        experiment.status_next = NimbusExperiment.Status.LIVE
        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, self.user, "test message")

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest_change()

        self.assertEqual(change.experiment, experiment)
        self.assertEqual(change.message, "test message")
        self.assertEqual(change.changed_by, self.user)
        self.assertEqual(change.old_status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(change.old_status_next, None)
        self.assertEqual(change.old_publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertEqual(change.new_status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(change.new_status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(change.new_publish_status, NimbusExperiment.PublishStatus.REVIEW)
        self.assertEqual(
            change.experiment_data,
            dict(NimbusExperimentChangeLogSerializer(experiment).data),
        )

    def test_no_change_to_published_dto(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            published_dto={"id": "experiment"},
        )

        change = generate_nimbus_changelog(experiment, self.user, "test message")

        self.assertFalse(change.published_dto_changed)

    def test_change_to_published_dto(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            published_dto={"id": "experiment", "test": False},
        )

        experiment.published_dto = {"id": "experiment", "test": True}

        change = generate_nimbus_changelog(experiment, self.user, "test message")

        self.assertTrue(change.published_dto_changed)

    def test_generates_changelog_with_out_of_date_latest_change(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        NimbusChangeLogFactory.create(
            experiment=experiment, experiment_data={"some_old": "data"}
        )
        generate_nimbus_changelog(experiment, self.user, "test message")
