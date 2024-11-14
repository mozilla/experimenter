import datetime
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.nimbus_ui_new.filtersets import SortChoices, TypeChoices
from experimenter.nimbus_ui_new.forms import QAStatusForm, TakeawaysForm
from experimenter.nimbus_ui_new.views import StatusChoices
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes
from experimenter.projects.tests.factories import ProjectFactory
from experimenter.segments import Segments
from experimenter.segments.tests import mock_valid_segments
from experimenter.targeting.constants import TargetingConstants


class AuthTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(email="user@example.com")
        self.client.defaults[settings.OPENIDC_EMAIL_HEADER] = self.user.email


class NimbusChangeLogsViewTest(AuthTestCase):
    def test_render_to_response(self):
        experiment = NimbusExperimentFactory.create(slug="test-experiment")
        response = self.client.get(
            reverse(
                "nimbus-new-history",
                kwargs={"slug": experiment.slug},
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["experiment"], experiment)


class NimbusExperimentsListViewTest(AuthTestCase):
    def test_render_to_response(self):
        for status in NimbusExperiment.Status:
            NimbusExperimentFactory.create(slug=status, status=status)

        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            slug="draft-review-experiment",
        )
        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            slug="live-review-experiment",
        )
        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.WAITING,
            slug="live-waiting-experiment",
        )
        NimbusExperimentFactory.create(is_archived=True, slug="archived-experiment")
        NimbusExperimentFactory.create(owner=self.user, slug="my-experiment")

        response = self.client.get(reverse("nimbus-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {e.slug for e in response.context["experiments"]},
            {
                e.slug
                for e in NimbusExperiment.objects.all().filter(
                    status=NimbusExperiment.Status.LIVE
                )
            },
        )
        self.assertDictEqual(
            dict(response.context["status_counts"]),
            {
                StatusChoices.ARCHIVED: 1,
                StatusChoices.COMPLETE: 1,
                StatusChoices.DRAFT: 3,
                StatusChoices.LIVE: 3,
                StatusChoices.MY_EXPERIMENTS: 3,
                StatusChoices.PREVIEW: 1,
                StatusChoices.REVIEW: 3,
            },
        )

    def test_status_counts_with_filters(self):
        for application in NimbusExperiment.Application:
            for status in NimbusExperiment.Status:
                NimbusExperimentFactory.create(status=status, application=application)

            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.DRAFT,
                publish_status=NimbusExperiment.PublishStatus.REVIEW,
                application=application,
            )
            NimbusExperimentFactory.create(is_archived=True, application=application)
            NimbusExperimentFactory.create(owner=self.user, application=application)

        response = self.client.get(
            reverse("nimbus-list"),
            {"application": NimbusExperiment.Application.DESKTOP},
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            dict(response.context["status_counts"]),
            {
                NimbusExperiment.Status.COMPLETE: 1,
                NimbusExperiment.Status.DRAFT: 3,
                NimbusExperiment.Status.LIVE: 1,
                NimbusExperiment.Status.PREVIEW: 1,
                "Review": 1,
                "Archived": 1,
                "MyExperiments": 1,
            },
        )

    @patch(
        "experimenter.nimbus_ui_new.views.NimbusExperimentsListView.paginate_by", new=3
    )
    def test_pagination(self):
        for _i in range(6):
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
            )

        response = self.client.get(reverse("nimbus-list"))
        self.assertEqual(len(response.context["experiments"]), 3)

        response = self.client.get(reverse("nimbus-list"), {"page": 2})
        self.assertEqual(len(response.context["experiments"]), 3)

    @parameterized.expand(
        (
            (
                StatusChoices.DRAFT,
                [
                    "my-experiment",
                    "subscribed-experiment",
                    NimbusExperiment.Status.DRAFT,
                    "draft-review-experiment",
                ],
            ),
            (StatusChoices.PREVIEW, [NimbusExperiment.Status.PREVIEW]),
            (
                StatusChoices.LIVE,
                [NimbusExperiment.Status.LIVE, "live-review-experiment"],
            ),
            (StatusChoices.COMPLETE, [NimbusExperiment.Status.COMPLETE]),
            (StatusChoices.REVIEW, ["draft-review-experiment", "live-review-experiment"]),
            (StatusChoices.ARCHIVED, ["archived-experiment"]),
            (StatusChoices.MY_EXPERIMENTS, ["my-experiment", "subscribed-experiment"]),
        )
    )
    def test_filter_status(self, filter_status, expected_slugs):
        for status in NimbusExperiment.Status:
            NimbusExperimentFactory.create(slug=status, status=status)

        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            slug="draft-review-experiment",
        )
        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            slug="live-review-experiment",
        )
        NimbusExperimentFactory.create(is_archived=True, slug="archived-experiment")
        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            owner=self.user,
            slug="my-experiment",
        )
        NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            slug="subscribed-experiment",
            subscribers=[self.user],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {"status": filter_status},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {e.slug for e in response.context["experiments"]},
            set(expected_slugs),
        )

    @parameterized.expand(
        (
            ("name",),
            ("slug",),
            ("public_description",),
            ("hypothesis",),
            ("takeaways_summary",),
            ("qa_comment",),
        )
    )
    def test_filter_search(self, field_name):
        test_string = "findme"
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, **{field_name: test_string}
        )
        [
            NimbusExperimentFactory.create(status=NimbusExperiment.Status.LIVE)
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {"status": NimbusExperiment.Status.LIVE, "search": test_string},
        )
        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    @parameterized.expand(
        (
            (TypeChoices.ROLLOUT, True),
            (TypeChoices.EXPERIMENT, False),
        )
    )
    def test_filter_type(self, type_choice, is_rollout):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, is_rollout=is_rollout
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, is_rollout=(not is_rollout)
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {"status": NimbusExperiment.Status.LIVE, "type": type_choice},
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_application(self):
        application = NimbusExperiment.Application.DESKTOP
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, application=application
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, application=a
            )
            for a in {*list(NimbusExperiment.Application)} - {application}
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {"status": NimbusExperiment.Status.LIVE, "application": application},
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_channel(self):
        channel = NimbusExperiment.Channel.NIGHTLY
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, channel=channel
        )
        [
            NimbusExperimentFactory.create(status=NimbusExperiment.Status.LIVE, channel=c)
            for c in {*list(NimbusExperiment.Channel)} - {channel}
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {"status": NimbusExperiment.Status.LIVE, "channel": channel},
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_version(self):
        version = NimbusExperiment.Version.FIREFOX_120
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, firefox_min_version=version
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, firefox_min_version=v
            )
            for v in {*list(NimbusExperiment.Version)} - {version}
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {"status": NimbusExperiment.Status.LIVE, "firefox_min_version": version},
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_feature_config(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            application=application,
            feature_configs=[feature_config],
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, application=application
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "feature_configs": feature_config.id,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_countries(self):
        country = CountryFactory.create()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, countries=[country]
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, countries=[]
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "countries": country.id,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_languages(self):
        language = LanguageFactory.create()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, languages=[language]
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, languages=[]
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "languages": language.id,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_locales(self):
        locale = LocaleFactory.create()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, locales=[locale]
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, locales=[]
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "locales": locale.id,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_targeting_config(self):
        targeting_config = TargetingConstants.TargetingConfig.EXISTING_USER
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            targeting_config_slug=targeting_config,
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE,
                targeting_config_slug=TargetingConstants.TargetingConfig.NO_TARGETING,
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "targeting_config_slug": targeting_config,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_projects(self):
        project = ProjectFactory.create()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, projects=[project]
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, projects=[]
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "projects": project.id,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_qa_status(self):
        qa_status = NimbusExperiment.QAStatus.GREEN
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            qa_status=qa_status,
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE,
                qa_status=NimbusExperiment.QAStatus.NOT_SET,
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "qa_status": qa_status,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    @parameterized.expand(
        (
            (NimbusExperiment.Takeaways.DAU_GAIN, "takeaways_metric_gain"),
            (NimbusExperiment.Takeaways.QBR_LEARNING, "takeaways_qbr_learning"),
            (
                NimbusExperiment.ConclusionRecommendation.FOLLOWUP,
                "conclusion_recommendations",
            ),
            (
                NimbusExperiment.ConclusionRecommendation.GRADUATE,
                "conclusion_recommendations",
            ),
        )
    )
    def test_filter_takeaways(self, takeaway_choice, takeaway_field):
        experiment_kwargs = (
            {takeaway_field: True}
            if takeaway_field != "conclusion_recommendations"
            else {"conclusion_recommendations": [takeaway_choice]}
        )
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, **experiment_kwargs
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE,
                **(
                    {takeaway_field: False}
                    if takeaway_field != "conclusion_recommendations"
                    else {"conclusion_recommendations": []}
                ),
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "takeaways": takeaway_choice,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_owner(self):
        owner = UserFactory.create()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, owner=owner
        )
        [
            NimbusExperimentFactory.create(status=NimbusExperiment.Status.LIVE)
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "owner": owner.id,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_subscribers(self):
        subscriber = UserFactory.create()
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE, subscribers=[subscriber]
        )
        [
            NimbusExperimentFactory.create(
                status=NimbusExperiment.Status.LIVE, subscribers=[]
            )
            for _i in range(3)
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "subscribers": subscriber.id,
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_default_sort_by_latest_update(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING
        )

        response = self.client.get(reverse("nimbus-list"))

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_name(self):
        experiment1 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            name="a",
        )
        experiment2 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            name="b",
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.NAME_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.NAME_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_qa(self):
        experiment1 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            qa_status=NimbusExperiment.QAStatus.GREEN,
        )
        experiment2 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            qa_status=NimbusExperiment.QAStatus.RED,
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.QA_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.QA_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_application(self):
        experiment1 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.FENIX,
        )
        experiment2 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.APPLICATION_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.APPLICATION_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_channel(self):
        experiment1 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            channel=NimbusExperiment.Channel.BETA,
        )
        experiment2 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            channel=NimbusExperiment.Channel.RELEASE,
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.CHANNEL_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.CHANNEL_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_size(self):
        experiment1 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            population_percent="0.0",
        )
        experiment2 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            population_percent="100.0",
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.SIZE_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.SIZE_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_features(self):
        feature1 = NimbusFeatureConfigFactory.create(slug="a")
        experiment1 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            feature_configs=[feature1],
        )
        feature2 = NimbusFeatureConfigFactory.create(slug="b")
        experiment2 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            feature_configs=[feature2],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.FEATURES_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.FEATURES_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_versions(self):
        experiment1 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
        )
        experiment2 = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_101,
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.VERSIONS_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.VERSIONS_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_dates(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=datetime.date(2024, 1, 1),
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=datetime.date(2024, 1, 2),
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.DATES_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.DATES_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )


class NimbusExperimentsListTableViewTest(AuthTestCase):
    def test_render_to_response(self):
        response = self.client.get(reverse("nimbus-new-table"))
        self.assertEqual(response.status_code, 200)

    def test_includes_request_get_parameters_in_response_header(self):
        response = self.client.get(
            reverse("nimbus-new-table"),
            {"status": "test"},
        )
        self.assertEqual(response.headers["HX-Push"], "?status=test")


class NimbusExperimentDetailViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create(
            slug="test-experiment",
            application="firefox-desktop",
            primary_outcomes=["outcome1", "outcome2"],
            secondary_outcomes=["outcome3", "outcome4"],
            segments=["segment1", "segment2"],
            risk_brand=True,
            qa_status="NOT_SET",
            takeaways_qbr_learning=True,
            takeaways_metric_gain=True,
            takeaways_summary="This is a summary.",
            takeaways_gain_amount="0.5% gain in retention",
            conclusion_recommendations=[
                NimbusExperiment.ConclusionRecommendation.RERUN,
                NimbusExperiment.ConclusionRecommendation.GRADUATE,
            ],
        )

    def test_render_to_response(self):
        response = self.client.get(
            reverse("nimbus-new-detail", kwargs={"slug": self.experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["experiment"], self.experiment)
        self.assertIn("RISK_QUESTIONS", response.context)

    def test_outcome_and_segment_links(self):
        response = self.client.get(
            reverse("nimbus-new-detail", kwargs={"slug": self.experiment.slug}),
        )
        expected_primary_links = [
            (
                "outcome1",
                "https://mozilla.github.io/metric-hub/outcomes/firefox-desktop/outcome1",
            ),
            (
                "outcome2",
                "https://mozilla.github.io/metric-hub/outcomes/firefox-desktop/outcome2",
            ),
        ]
        expected_secondary_links = [
            (
                "outcome3",
                "https://mozilla.github.io/metric-hub/outcomes/firefox-desktop/outcome3",
            ),
            (
                "outcome4",
                "https://mozilla.github.io/metric-hub/outcomes/firefox-desktop/outcome4",
            ),
        ]
        expected_segment_links = [
            (
                "segment1",
                "https://mozilla.github.io/metric-hub/segments/firefox_desktop/#segment1",
            ),
            (
                "segment2",
                "https://mozilla.github.io/metric-hub/segments/firefox_desktop/#segment2",
            ),
        ]

        self.assertEqual(
            response.context["primary_outcome_links"], expected_primary_links
        )
        self.assertEqual(
            response.context["secondary_outcome_links"], expected_secondary_links
        )
        self.assertEqual(response.context["segment_links"], expected_segment_links)

    def test_qa_edit_mode_get(self):
        response = self.client.get(
            reverse("nimbus-new-detail", kwargs={"slug": self.experiment.slug}),
            {"edit_qa_status": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["qa_edit_mode"])
        self.assertIsInstance(response.context["form"], QAStatusForm)

    def test_qa_edit_mode_post_valid_form(self):
        data = {
            "qa_status": "GREEN",
            "qa_comment": "Everything looks good.",
        }
        response = self.client.post(
            reverse("update-qa-status", kwargs={"slug": self.experiment.slug}),
            data,
        )
        self.assertEqual(response.status_code, 302)  # redirect
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.qa_status, "GREEN")
        self.assertEqual(self.experiment.qa_comment, "Everything looks good.")

    def test_qa_edit_mode_post_invalid_form(self):
        data = {
            "qa_status": "INVALID_STATUS",  # Invalid QAStatus choice
            "qa_comment": "Invalid status.",
        }
        response = self.client.post(
            reverse("update-qa-status", kwargs={"slug": self.experiment.slug}),
            data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["qa_edit_mode"])
        self.assertIsInstance(response.context["form"], QAStatusForm)
        self.assertFalse(response.context["form"].is_valid())
        # Ensure changes are not saved to the database
        self.experiment.refresh_from_db()
        self.assertNotEqual(self.experiment.qa_status, "INVALID_STATUS")
        self.assertEqual(self.experiment.qa_status, "NOT_SET")

    def test_takeaways_card(self):
        response = self.client.get(
            reverse("nimbus-new-detail", kwargs={"slug": self.experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, NimbusExperiment.Takeaways.QBR_LEARNING)
        self.assertContains(response, NimbusExperiment.Takeaways.DAU_GAIN)
        self.assertContains(response, self.experiment.takeaways_summary)
        self.assertContains(response, self.experiment.takeaways_gain_amount)
        self.assertContains(
            response, NimbusExperiment.ConclusionRecommendation.GRADUATE.label
        )
        self.assertContains(
            response, NimbusExperiment.ConclusionRecommendation.RERUN.label
        )

    def test_takeaways_edit_mode_get(self):
        response = self.client.get(
            reverse("nimbus-new-detail", kwargs={"slug": self.experiment.slug}),
            {"edit_takeaways": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["takeaways_edit_mode"])
        self.assertIsInstance(response.context["takeaways_form"], TakeawaysForm)

    def test_takeaways_edit_mode_post_valid_form(self):
        data = {
            "takeaways_qbr_learning": True,
            "takeaways_metric_gain": True,
            "takeaways_summary": "Updated summary.",
            "takeaways_gain_amount": "1% gain in retention",
            "conclusion_recommendations": [
                NimbusExperiment.ConclusionRecommendation.CHANGE_COURSE,
                NimbusExperiment.ConclusionRecommendation.FOLLOWUP,
            ],
        }
        response = self.client.post(
            reverse("update-takeaways", kwargs={"slug": self.experiment.slug}),
            data,
        )
        self.assertEqual(response.status_code, 302)  # redirect
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.takeaways_summary, "Updated summary.")
        self.assertEqual(self.experiment.takeaways_gain_amount, "1% gain in retention")
        self.assertListEqual(
            self.experiment.conclusion_recommendations,
            [
                NimbusExperiment.ConclusionRecommendation.CHANGE_COURSE,
                NimbusExperiment.ConclusionRecommendation.FOLLOWUP,
            ],
        )

    def test_takeaways_edit_mode_post_invalid_form(self):
        data = {
            "takeaways_qbr_learning": True,
            "takeaways_metric_gain": True,
            "takeaways_summary": "Updated summary.",
            "takeaways_gain_amount": "1% gain in retention",
            "conclusion_recommendations": [
                "INVALID_CHOICE",  # Invalid conclusion recommendation choice
            ],
        }
        response = self.client.post(
            reverse("update-takeaways", kwargs={"slug": self.experiment.slug}),
            data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["takeaways_edit_mode"])
        self.assertIsInstance(response.context["takeaways_form"], TakeawaysForm)
        self.assertFalse(response.context["takeaways_form"].is_valid())

    def test_signoff_edit_mode_post_valid_form(self):
        data = {
            "qa_signoff": True,
            "vp_signoff": True,
            "legal_signoff": True,
        }
        response = self.client.post(
            reverse("update-signoff", kwargs={"slug": self.experiment.slug}),
            data,
        )
        self.assertEqual(response.status_code, 302)
        self.experiment.refresh_from_db()
        self.assertTrue(self.experiment.qa_signoff)
        self.assertTrue(self.experiment.vp_signoff)
        self.assertTrue(self.experiment.legal_signoff)

    def test_subscribe_to_experiment(self):
        self.assertNotIn(self.user, self.experiment.subscribers.all())

        response = self.client.post(
            reverse("nimbus-new-subscribe", kwargs={"slug": self.experiment.slug})
        )

        self.experiment.refresh_from_db()

        self.assertIn(self.user, self.experiment.subscribers.all())
        self.assertEqual(response.status_code, 200)

    def test_unsubscribe_from_experiment(self):
        self.experiment.subscribers.add(self.user)
        self.experiment.save()

        self.assertIn(self.user, self.experiment.subscribers.all())

        response = self.client.post(
            reverse("nimbus-new-unsubscribe", kwargs={"slug": self.experiment.slug})
        )

        self.experiment.refresh_from_db()

        self.assertNotIn(self.user, self.experiment.subscribers.all())
        self.assertEqual(response.status_code, 200)


class TestNimbusExperimentsCreateView(AuthTestCase):
    def test_post_creates_experiment(self):
        response = self.client.post(
            reverse("nimbus-new-create"),
            {
                "name": "Test Experiment",
                "hypothesis": "test",
                "application": NimbusExperiment.Application.DESKTOP,
            },
        )
        self.assertEqual(response.status_code, 200)
        experiment = NimbusExperiment.objects.get(slug="test-experiment")
        self.assertEqual(experiment.hypothesis, "test")
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.owner, self.user)


@mock_valid_outcomes
@mock_valid_segments
class TestMetricsUpdateView(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Outcomes.clear_cache()

    def test_get_renders_page(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        response = self.client.get(
            reverse("nimbus-new-update-metrics", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_post_updates_metrics_and_segments(self):
        application = NimbusExperiment.Application.DESKTOP
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            primary_outcomes=[],
            secondary_outcomes=[],
            segments=[],
        )
        outcomes = Outcomes.by_application(application)
        segments = Segments.by_application(application)

        outcome1 = outcomes[0]
        outcome2 = outcomes[1]
        segment1 = segments[0]
        segment2 = segments[1]

        response = self.client.post(
            reverse("nimbus-new-update-metrics", kwargs={"slug": experiment.slug}),
            {
                "primary_outcomes": [outcome1.slug],
                "secondary_outcomes": [outcome2.slug],
                "segments": [segment1.slug, segment2.slug],
            },
        )

        self.assertEqual(response.status_code, 200)
        experiment = NimbusExperiment.objects.get(slug=experiment.slug)
        self.assertEqual(experiment.primary_outcomes, [outcome1.slug])
        self.assertEqual(experiment.secondary_outcomes, [outcome2.slug])
        self.assertEqual(experiment.segments, [segment1.slug, segment2.slug])
