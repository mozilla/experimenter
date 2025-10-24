import datetime
import json
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
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
    NimbusFeatureConfig,
)
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.klaatu.tasks import klaatu_start_job
from experimenter.nimbus_ui.filtersets import (
    FeaturesPageSortChoices,
    MyDeliveriesChoices,
    SortChoices,
    TypeChoices,
)
from experimenter.nimbus_ui.forms import QAStatusForm, TakeawaysForm
from experimenter.nimbus_ui.views import StatusChoices
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes
from experimenter.projects.tests.factories import ProjectFactory
from experimenter.segments import Segments
from experimenter.segments.tests.mock_segments import mock_get_segments
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
                "nimbus-ui-history",
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

    @patch("experimenter.nimbus_ui.views.NimbusExperimentsListView.paginate_by", new=3)
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
            (
                TypeChoices.ROLLOUT,
                {"slug": "experiment", "is_rollout": True},
                [
                    {"slug": "rollout", "is_rollout": False},
                    {
                        "slug": "labs",
                        "is_rollout": True,
                        "is_firefox_labs_opt_in": True,
                        "firefox_labs_title": "title",
                        "firefox_labs_description": "description",
                        "firefox_labs_group": (
                            NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING
                        ),
                    },
                ],
            ),
            (
                TypeChoices.EXPERIMENT,
                {"slug": "experiment"},
                [
                    {"slug": "rollout", "is_rollout": True},
                    {
                        "slug": "labs",
                        "is_firefox_labs_opt_in": True,
                        "firefox_labs_title": "title",
                        "firefox_labs_description": "description",
                        "firefox_labs_group": (
                            NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING
                        ),
                    },
                ],
            ),
            (
                TypeChoices.LABS,
                {
                    "slug": "labs",
                    "is_firefox_labs_opt_in": True,
                    "firefox_labs_title": "title",
                    "firefox_labs_description": "description",
                    "firefox_labs_group": (
                        NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING
                    ),
                },
                [{"slug": "experiment"}, {"slug": "rollout", "is_rollout": True}],
            ),
        )
    )
    def test_filter_type(self, type_choice, experiment_kwargs, other_experiments):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            **experiment_kwargs,
        )

        for kwargs in other_experiments:
            NimbusExperimentFactory.create(status=NimbusExperiment.Status.LIVE, **kwargs)

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
            application=NimbusExperiment.Application.FENIX,
            slug=f"channel-{channel}",
            status=NimbusExperiment.Status.LIVE,
            channel=channel,
            channels=[],
        )
        [
            NimbusExperimentFactory.create(
                application=NimbusExperiment.Application.FENIX,
                slug=f"channel-{c}",
                status=NimbusExperiment.Status.LIVE,
                channel=c,
                channels=[],
            )
            for c in {*list(NimbusExperiment.Channel)} - {channel}
        ]

        response = self.client.get(
            reverse("nimbus-list"),
            {"status": NimbusExperiment.Status.LIVE, "channel": channel},
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]}, {experiment.slug}
        )

    def test_filter_channels(self):
        experiment_nightly = NimbusExperimentFactory.create(
            slug="nightly",
            status=NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.NIGHTLY,
            channels=[],
        )
        experiment_nightly_beta = NimbusExperimentFactory.create(
            slug="nightly-beta",
            status=NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            channels=[NimbusExperiment.Channel.NIGHTLY, NimbusExperiment.Channel.BETA],
        )
        experiment_release_beta = NimbusExperimentFactory.create(
            slug="release-beta",
            status=NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            channels=[NimbusExperiment.Channel.RELEASE, NimbusExperiment.Channel.BETA],
        )
        experiment_release_dev = NimbusExperimentFactory.create(
            slug="release-dev",
            status=NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            channels=[
                NimbusExperiment.Channel.RELEASE,
                NimbusExperiment.Channel.DEVELOPER,
            ],
        )
        NimbusExperimentFactory.create(
            slug="aurora-dev",
            status=NimbusExperiment.Status.LIVE,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            channels=[
                NimbusExperiment.Channel.AURORA,
                NimbusExperiment.Channel.DEVELOPER,
            ],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.LIVE,
                "channel": [
                    NimbusExperiment.Channel.NIGHTLY,
                    NimbusExperiment.Channel.RELEASE,
                ],
            },
        )

        self.assertEqual(
            {e.slug for e in response.context["experiments"]},
            {
                experiment_nightly.slug,
                experiment_nightly_beta.slug,
                experiment_release_beta.slug,
                experiment_release_dev.slug,
            },
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
            application=NimbusExperiment.Application.DESKTOP,
            slug="desktop-beta",
            status=NimbusExperiment.Status.LIVE,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            channels=[NimbusExperiment.Channel.BETA],
        )
        experiment2 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="desktop-release",
            status=NimbusExperiment.Status.LIVE,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            channels=[NimbusExperiment.Channel.RELEASE],
        )
        experiment3 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.FENIX,
            slug="fenix-beta",
            status=NimbusExperiment.Status.LIVE,
            channel=NimbusExperiment.Channel.BETA,
            channels=[],
        )
        experiment4 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.FENIX,
            slug="fenix-release",
            status=NimbusExperiment.Status.LIVE,
            channel=NimbusExperiment.Channel.RELEASE,
            channels=[],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.CHANNEL_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment3.slug, experiment2.slug, experiment4.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.CHANNEL_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment4.slug, experiment1.slug, experiment3.slug],
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

    def test_sort_by_start_date(self):
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
                "sort": SortChoices.START_DATE_UP,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "sort": SortChoices.START_DATE_DOWN,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_sort_by_end_date(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            slug="experiment-1",
            start_date=datetime.date(2024, 1, 3),
            end_date=datetime.date(2024, 2, 1),
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            slug="experiment-2",
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 2, 3),
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.COMPLETE,
                "sort": SortChoices.END_DATE_UP,
            },
        )
        filtered_response = [
            e.slug
            for e in response.context["experiments"]
            if e.slug in ["experiment-1", "experiment-2"]
        ]

        self.assertEqual(
            filtered_response,
            ([experiment1.slug, experiment2.slug]),
        )

        response = self.client.get(
            reverse("nimbus-list"),
            {
                "status": NimbusExperiment.Status.COMPLETE,
                "sort": SortChoices.END_DATE_DOWN,
            },
        )

        filtered_response = [
            e.slug
            for e in response.context["experiments"]
            if e.slug in ["experiment-1", "experiment-2"]
        ]

        self.assertEqual(
            filtered_response,
            ([experiment2.slug, experiment1.slug]),
        )


class NimbusExperimentsListTableViewTest(AuthTestCase):
    def test_render_to_response(self):
        response = self.client.get(reverse("nimbus-ui-table"))
        self.assertEqual(response.status_code, 200)

    def test_includes_request_get_parameters_in_response_header(self):
        response = self.client.get(
            reverse("nimbus-ui-table"),
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
            reverse("nimbus-ui-detail", kwargs={"slug": self.experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["experiment"], self.experiment)
        self.assertIn("RISK_QUESTIONS", response.context)

    def test_save_failed_query_arg_passed_in_context(self):
        response = self.client.get(
            reverse("nimbus-ui-detail", kwargs={"slug": self.experiment.slug}),
            {"save_failed": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["save_failed"])

    def test_outcome_and_segment_links(self):
        response = self.client.get(
            reverse("nimbus-ui-detail", kwargs={"slug": self.experiment.slug}),
        )
        expected_primary_links = [
            (
                "outcome1",
                "https://mozilla.github.io/metric-hub/outcomes/firefox_desktop/outcome1",
            ),
            (
                "outcome2",
                "https://mozilla.github.io/metric-hub/outcomes/firefox_desktop/outcome2",
            ),
        ]
        expected_secondary_links = [
            (
                "outcome3",
                "https://mozilla.github.io/metric-hub/outcomes/firefox_desktop/outcome3",
            ),
            (
                "outcome4",
                "https://mozilla.github.io/metric-hub/outcomes/firefox_desktop/outcome4",
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
            reverse("nimbus-ui-detail", kwargs={"slug": self.experiment.slug}),
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
            reverse("nimbus-ui-update-qa-status", kwargs={"slug": self.experiment.slug}),
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
            reverse("nimbus-ui-update-qa-status", kwargs={"slug": self.experiment.slug}),
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
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            slug="experiment",
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 2, 3),
            takeaways_qbr_learning=True,
            takeaways_metric_gain=True,
            takeaways_summary="This is a summary.",
            takeaways_gain_amount="0.5% gain in retention",
            conclusion_recommendations=[
                NimbusExperiment.ConclusionRecommendation.RERUN,
                NimbusExperiment.ConclusionRecommendation.GRADUATE,
            ],
        )
        response = self.client.get(
            reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, NimbusExperiment.Takeaways.QBR_LEARNING)
        self.assertContains(response, NimbusExperiment.Takeaways.DAU_GAIN)
        self.assertContains(response, experiment.takeaways_summary)
        self.assertContains(response, experiment.takeaways_gain_amount)
        self.assertContains(
            response, NimbusExperiment.ConclusionRecommendation.GRADUATE.label
        )
        self.assertContains(
            response, NimbusExperiment.ConclusionRecommendation.RERUN.label
        )

    def test_takeaways_edit_mode_get(self):
        response = self.client.get(
            reverse("nimbus-ui-detail", kwargs={"slug": self.experiment.slug}),
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
            reverse("nimbus-ui-update-takeaways", kwargs={"slug": self.experiment.slug}),
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
            reverse("nimbus-ui-update-takeaways", kwargs={"slug": self.experiment.slug}),
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
            reverse("nimbus-ui-update-signoff", kwargs={"slug": self.experiment.slug}),
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
            reverse("nimbus-ui-subscribe", kwargs={"slug": self.experiment.slug})
        )

        self.experiment.refresh_from_db()

        self.assertIn(self.user, self.experiment.subscribers.all())
        self.assertEqual(response.status_code, 200)

    def test_unsubscribe_from_experiment(self):
        self.experiment.subscribers.add(self.user)
        self.experiment.save()

        self.assertIn(self.user, self.experiment.subscribers.all())

        response = self.client.post(
            reverse("nimbus-ui-unsubscribe", kwargs={"slug": self.experiment.slug})
        )

        self.experiment.refresh_from_db()

        self.assertNotIn(self.user, self.experiment.subscribers.all())
        self.assertEqual(response.status_code, 200)

    def test_ready_is_false_if_review_serializer_invalid(self):
        experiment = NimbusExperimentFactory.create(
            public_description="",
            population_percent=0,
            total_enrolled_clients=0,
            proposed_enrollment=0,
            proposed_duration=0,
            hypothesis=NimbusExperiment.HYPOTHESIS_DEFAULT,
            feature_configs=[],
        )

        response = self.client.get(
            reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("validation_errors", response.context)
        self.assertEqual(
            set(response.context["invalid_pages"]), {"overview", "branches", "audience"}
        )
        self.assertFalse(
            response.context["is_ready_to_launch"],
            "`is_ready_to_launch` should be False when the review serializer is invalid",
        )

    def test_ready_is_false_if_review_serializer_invalid_for_metrics(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
            primary_outcomes=["outcome"],
            secondary_outcomes=["outcome"],
        )

        response = self.client.get(
            reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("validation_errors", response.context)
        self.assertEqual(
            set(response.context["invalid_pages"]),
            {"metrics"},
            response.context["validation_errors"],
        )
        self.assertFalse(
            response.context["is_ready_to_launch"],
            "`is_ready_to_launch` should be False when the review serializer is invalid",
        )


class TestNimbusExperimentsCreateView(AuthTestCase):
    def test_post_creates_experiment(self):
        response = self.client.post(
            reverse("nimbus-ui-create"),
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


class TestNimbusExperimentsSidebarCloneView(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create(
            slug="test-experiment",
            application="firefox-desktop",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
        )

    def test_post_clones_experiment(self):
        response = self.client.post(
            reverse("nimbus-ui-clone", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user, "name": "Test Experiment Copy"},
        )
        self.assertEqual(response.status_code, 200)
        experiment = NimbusExperiment.objects.get(slug="test-experiment-copy")
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.FIREFOX_120
        )

    def test_post_passes_experiment(self):
        response = self.client.post(
            reverse("nimbus-ui-clone", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user, "name": "Test Experiment"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context["experiment"], self.experiment)

    def test_form_invalid_renders_with_experiment_context(self):
        response = self.client.post(
            reverse("nimbus-ui-clone", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user, "name": "$."},
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context["form"].errors)

        self.assertIn("experiment", response.context)
        self.assertEqual(response.context["experiment"], self.experiment)


class TestNimbusExperimentPromoteToRolloutView(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create(
            slug="test-experiment",
            application="firefox-desktop",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
        )

    def test_post_clones_experiment(self):
        response = self.client.post(
            reverse(
                "nimbus-ui-promote-to-rollout",
                kwargs={"slug": self.experiment.slug, "branch": "control"},
            ),
            {"owner": self.user, "name": "Test Experiment Copy"},
        )
        self.assertEqual(response.status_code, 200)
        experiment = NimbusExperiment.objects.get(slug="test-experiment-copy")
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.FIREFOX_120
        )

    def test_post_passes_experiment(self):
        response = self.client.post(
            reverse("nimbus-ui-clone", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user, "name": "Test Experiment"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context["experiment"], self.experiment)

    def test_form_invalid_renders_with_experiment_context(self):
        response = self.client.post(
            reverse("nimbus-ui-clone", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user, "name": "$."},
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(response.context["form"].errors)

        self.assertIn("experiment", response.context)
        self.assertEqual(response.context["experiment"], self.experiment)


class TestToggleArchiveView(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperiment.objects.create(
            slug="test-experiment",
            name="Test Experiment",
            owner=self.user,
            is_archived=False,
        )

    def test_toggle_archive_status_to_archive(self):
        response = self.client.post(
            reverse("nimbus-ui-toggle-archive", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Refresh"), "true")

        updated_experiment = NimbusExperiment.objects.get(slug=self.experiment.slug)
        self.assertTrue(updated_experiment.is_archived)

    def test_toggle_archive_status_to_unarchive(self):
        self.experiment.is_archived = True
        self.experiment.save()

        response = self.client.post(
            reverse("nimbus-ui-toggle-archive", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Refresh"), "true")

        updated_experiment = NimbusExperiment.objects.get(slug=self.experiment.slug)
        self.assertFalse(updated_experiment.is_archived)


class TestOverviewUpdateView(AuthTestCase):
    def test_get_renders_for_draft_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        response = self.client.get(
            reverse("nimbus-ui-update-overview", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_get_non_draft_redirects_to_summary(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        response = self.client.get(
            reverse("nimbus-ui-update-overview", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug})
        )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_post_non_draft_hx_redirects_to_summary(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        response = self.client.post(
            reverse("nimbus-ui-update-overview", kwargs={"slug": experiment.slug}), {}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("HX-Redirect"),
            (
                f"{reverse('nimbus-ui-detail', kwargs={'slug': experiment.slug})}"
                "?save_failed=true"
            ),
        )

    def test_post_updates_overview(self):
        project = ProjectFactory.create()
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )

        response = self.client.post(
            reverse("nimbus-ui-update-overview", kwargs={"slug": experiment.slug}),
            {
                "name": "new name",
                "hypothesis": "new hypothesis",
                "risk_brand": True,
                "risk_message": True,
                "projects": [project.id],
                "public_description": "new description",
                "risk_revenue": True,
                "risk_partner_related": True,
                # Management form data for the inline formset
                "documentation_links-TOTAL_FORMS": "1",
                "documentation_links-INITIAL_FORMS": "1",
                "documentation_links-0-id": documentation_link.id,
                "documentation_links-0-title": (
                    NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                ),
                "documentation_links-0-link": "https://www.example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        experiment = NimbusExperiment.objects.get(slug=experiment.slug)

        self.assertEqual(experiment.name, "new name")
        self.assertEqual(experiment.hypothesis, "new hypothesis")
        self.assertTrue(experiment.risk_brand)
        self.assertTrue(experiment.risk_message)
        self.assertEqual(list(experiment.projects.all()), [project])
        self.assertEqual(experiment.public_description, "new description")
        self.assertTrue(experiment.risk_revenue)
        self.assertTrue(experiment.risk_partner_related)

        documentation_link = experiment.documentation_links.all().get()
        self.assertEqual(
            documentation_link.title, NimbusExperiment.DocumentationLink.DESIGN_DOC
        )
        self.assertEqual(documentation_link.link, "https://www.example.com")

    def test_invalid_form_fields_with_show_errors(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )
        base_url = reverse("nimbus-ui-update-overview", kwargs={"slug": experiment.slug})
        response = self.client.post(
            f"{base_url}?show_errors=true",
            {
                "name": "test-experiment",
                "hypothesis": "",
                "public_description": "",
                "risk_partner_related": "",
                "risk_revenue": "",
                "risk_brand": "",
                "risk_message": "",
                "projects": [],
                "documentation_links-TOTAL_FORMS": "1",
                "documentation_links-INITIAL_FORMS": "1",
                "documentation_links-0-id": documentation_link.id,
                "documentation_links-0-title": (
                    NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                ),
                "documentation_links-0-link": "https://www.example.com",
            },
        )

        self.assertEqual(response.status_code, 200)

        validation_errors = response.context["validation_errors"]
        self.assertIn("This field may not be blank.", validation_errors["hypothesis"])
        self.assertIn(
            "This field may not be blank.", validation_errors["public_description"]
        )
        self.assertIn(
            "This question may not be blank.", validation_errors["risk_partner_related"]
        )
        self.assertIn(
            "This question may not be blank.", validation_errors["risk_revenue"]
        )
        self.assertIn("This question may not be blank.", validation_errors["risk_brand"])
        self.assertIn(
            "This question may not be blank.", validation_errors["risk_message"]
        )

    def test_invalid_form_fields_without_show_errors(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )
        response = self.client.post(
            reverse("nimbus-ui-update-overview", kwargs={"slug": experiment.slug}),
            {
                "name": "test-experiment",
                "hypothesis": "",
                "public_description": "",
                "risk_partner_related": "",
                "risk_revenue": "",
                "risk_brand": "",
                "risk_message": "",
                "projects": [],
                "documentation_links-TOTAL_FORMS": "1",
                "documentation_links-INITIAL_FORMS": "1",
                "documentation_links-0-id": documentation_link.id,
                "documentation_links-0-title": (
                    NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                ),
                "documentation_links-0-link": "https://www.example.com",
            },
        )

        self.assertEqual(response.status_code, 200)

        validation_errors = response.context["validation_errors"]
        self.assertEqual(validation_errors, {})


class TestDocumentationLinkCreateView(AuthTestCase):
    def test_post_creates_documentation_link(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[],
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-create-documentation-link", kwargs={"slug": experiment.slug}
            ),
            {
                "name": "new name",
                "hypothesis": "new hypothesis",
                "risk_brand": True,
                "risk_message": True,
                "projects": [],
                "public_description": "new description",
                "risk_revenue": True,
                "risk_partner_related": True,
                # Management form data for the inline formset
                "documentation_links-TOTAL_FORMS": "0",
                "documentation_links-INITIAL_FORMS": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(experiment.documentation_links.all().count(), 1)


class TestDocumentationLinkDeleteView(AuthTestCase):
    def test_post_deletes_documentation_link(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-delete-documentation-link", kwargs={"slug": experiment.slug}
            ),
            {
                "name": "new name",
                "hypothesis": "new hypothesis",
                "risk_brand": True,
                "risk_message": True,
                "projects": [],
                "public_description": "new description",
                "risk_revenue": True,
                "risk_partner_related": True,
                # Management form data for the inline formset
                "documentation_links-TOTAL_FORMS": "1",
                "documentation_links-INITIAL_FORMS": "1",
                "documentation_links-0-id": documentation_link.id,
                "documentation_links-0-title": (
                    NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                ),
                "documentation_links-0-link": "https://www.example.com",
                "link_id": documentation_link.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(experiment.documentation_links.all().count(), 0)


class TestBranchesUpdateViews(AuthTestCase):
    def test_get_renders_for_draft_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        response = self.client.get(
            reverse("nimbus-ui-update-branches", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_get_non_draft_redirects_to_summary(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        response = self.client.get(
            reverse("nimbus-ui-update-branches", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug})
        )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_post_non_draft_hx_redirects_to_summary(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        response = self.client.post(
            reverse("nimbus-ui-update-branches", kwargs={"slug": experiment.slug}), {}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("HX-Redirect"),
            (
                f"{reverse('nimbus-ui-detail', kwargs={'slug': experiment.slug})}"
                "?save_failed=true"
            ),
        )

    @parameterized.expand(
        [
            ("nimbus-ui-partial-update-branches",),
            ("nimbus-ui-update-branches",),
        ]
    )
    def test_post_updates_branches(self, url):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
            is_localized=False,
            localizations=None,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        reference_screenshot = reference_branch.screenshots.first()
        treatment_screenshot = treatment_branch.screenshots.first()

        data = {
            "feature_configs": [feature_config1.id, feature_config2.id],
            "equal_branch_ratio": False,
            "branches-TOTAL_FORMS": "2",
            "branches-INITIAL_FORMS": "2",
            "branches-MIN_NUM_FORMS": "0",
            "branches-MAX_NUM_FORMS": "1000",
            "branches-0-id": reference_branch.id,
            "branches-0-name": "Control",
            "branches-0-description": "Control Description",
            "branches-0-ratio": 2,
            "branches-0-feature-value-TOTAL_FORMS": "2",
            "branches-0-feature-value-INITIAL_FORMS": "2",
            "branches-0-feature-value-MIN_NUM_FORMS": "0",
            "branches-0-feature-value-MAX_NUM_FORMS": "1000",
            "branches-0-feature-value-0-id": reference_branch_feature_config1_value.id,
            "branches-0-feature-value-0-value": json.dumps(
                {"control-feature1-key": "control-feature-1-value"}
            ),
            "branches-0-feature-value-1-id": reference_branch_feature_config2_value.id,
            "branches-0-feature-value-1-value": json.dumps(
                {"control-feature-2-key": "control-feature-2-value"}
            ),
            "branches-0-screenshots-TOTAL_FORMS": "1",
            "branches-0-screenshots-INITIAL_FORMS": "1",
            "branches-0-screenshots-MIN_NUM_FORMS": "0",
            "branches-0-screenshots-MAX_NUM_FORMS": "1000",
            "branches-0-screenshots-0-id": reference_screenshot.id,
            "branches-0-screenshots-0-description": "Updated control screenshot",
            "branches-0-screenshots-0-image": "",
            "branches-1-id": treatment_branch.id,
            "branches-1-name": "Treatment",
            "branches-1-description": "Treatment Description",
            "branches-1-ratio": 3,
            "branches-1-feature-value-TOTAL_FORMS": "2",
            "branches-1-feature-value-INITIAL_FORMS": "2",
            "branches-1-feature-value-MIN_NUM_FORMS": "0",
            "branches-1-feature-value-MAX_NUM_FORMS": "1000",
            "branches-1-feature-value-0-id": treatment_branch_feature_config1_value.id,
            "branches-1-feature-value-0-value": json.dumps(
                {"treatment-feature-1-key": "treatment-feature-1-value"}
            ),
            "branches-1-feature-value-1-id": treatment_branch_feature_config2_value.id,
            "branches-1-feature-value-1-value": json.dumps(
                {"treatment-feature-2-key": "treatment-feature-2-value"}
            ),
            "branches-1-screenshots-TOTAL_FORMS": "1",
            "branches-1-screenshots-INITIAL_FORMS": "1",
            "branches-1-screenshots-MIN_NUM_FORMS": "0",
            "branches-1-screenshots-MAX_NUM_FORMS": "1000",
            "branches-1-screenshots-0-id": treatment_screenshot.id,
            "branches-1-screenshots-0-description": "Updated treatment screenshot",
            "branches-1-screenshots-0-image": "",
            "is_localized": True,
            "localizations": json.dumps({"localization-key": "localization-value"}),
        }

        response = self.client.post(reverse(url, kwargs={"slug": experiment.slug}), data)

        self.assertEqual(response.status_code, 200)
        experiment = NimbusExperiment.objects.get(slug=experiment.slug)

        self.assertEqual(
            set(experiment.feature_configs.all()), {feature_config1, feature_config2}
        )
        self.assertFalse(experiment.equal_branch_ratio)
        self.assertTrue(experiment.is_localized)
        self.assertEqual(
            experiment.localizations,
            json.dumps({"localization-key": "localization-value"}),
        )
        self.assertEqual(experiment.reference_branch.name, "Control")
        self.assertEqual(experiment.reference_branch.slug, "control")
        self.assertEqual(experiment.reference_branch.description, "Control Description")
        self.assertEqual(experiment.reference_branch.ratio, 2)
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config1
            )
            .get()
            .value,
            json.dumps({"control-feature1-key": "control-feature-1-value"}),
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config2
            )
            .get()
            .value,
            json.dumps({"control-feature-2-key": "control-feature-2-value"}),
        )
        # Assert screenshot descriptions updated
        self.assertEqual(
            experiment.reference_branch.screenshots.get(
                id=reference_screenshot.id
            ).description,
            "Updated control screenshot",
        )
        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "Treatment")
        self.assertEqual(treatment_branch.slug, "treatment")
        self.assertEqual(treatment_branch.description, "Treatment Description")
        self.assertEqual(treatment_branch.ratio, 3)
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config1)
            .get()
            .value,
            json.dumps({"treatment-feature-1-key": "treatment-feature-1-value"}),
        )
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config2)
            .get()
            .value,
            json.dumps({"treatment-feature-2-key": "treatment-feature-2-value"}),
        )
        self.assertEqual(
            treatment_branch.screenshots.get(id=treatment_screenshot.id).description,
            "Updated treatment screenshot",
        )
        changelog = experiment.changes.get()
        self.assertIn("updated branches", changelog.message)


class TestBranchCreateView(AuthTestCase):
    def test_post_creates_branch(self):
        feature_config1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature_config2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config1, feature_config2],
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()
        experiment.reference_branch = None
        experiment.save()

        response = self.client.post(
            reverse("nimbus-ui-create-branch", kwargs={"slug": experiment.slug}),
            {
                "feature_configs": [feature_config1.id, feature_config2.id],
            },
        )

        self.assertEqual(response.status_code, 200)
        experiment = NimbusExperiment.objects.get(slug=experiment.slug)

        self.assertEqual(experiment.reference_branch.name, "Control")
        self.assertEqual(experiment.reference_branch.slug, "control")
        self.assertEqual(experiment.reference_branch.description, "")
        self.assertEqual(experiment.reference_branch.ratio, 1)
        self.assertEqual(experiment.reference_branch.feature_values.count(), 2)
        self.assertEqual(
            set(
                experiment.reference_branch.feature_values.values_list(
                    "feature_config", flat=True
                )
            ),
            {feature_config1.id, feature_config2.id},
        )

        change = experiment.changes.get()
        self.assertIn("added a branch", change.message)


class TestBranchDeleteView(AuthTestCase):
    def test_post_deletes_branch(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment.changes.all().delete()

        branch_count = experiment.branches.count()

        response = self.client.post(
            reverse("nimbus-ui-delete-branch", kwargs={"slug": experiment.slug}),
            {"branch_id": experiment.treatment_branches[0].id},
        )
        self.assertEqual(response.status_code, 200)

        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(experiment.branches.count(), branch_count - 1)
        self.assertEqual(experiment.changes.count(), 1)
        self.assertIn("removed a branch", experiment.changes.get().message)


@mock_valid_outcomes
class TestMetricsUpdateView(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Outcomes.clear_cache()

    def test_get_renders_for_draft_experiment(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        response = self.client.get(
            reverse("nimbus-ui-update-metrics", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_get_non_draft_redirects_to_summary(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        response = self.client.get(
            reverse("nimbus-ui-update-metrics", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug})
        )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_post_non_draft_hx_redirects_to_summary(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle)
        response = self.client.post(
            reverse("nimbus-ui-update-metrics", kwargs={"slug": experiment.slug}), {}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("HX-Redirect"),
            (
                f"{reverse('nimbus-ui-detail', kwargs={'slug': experiment.slug})}"
                "?save_failed=true"
            ),
        )

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
        segments = Segments.by_application(application, mock_get_segments())

        outcome1 = outcomes[0]
        outcome2 = outcomes[1]
        segment1 = segments[0]
        segment2 = segments[1]

        response = self.client.post(
            reverse("nimbus-ui-update-metrics", kwargs={"slug": experiment.slug}),
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

    def test_invalid_metrics_page_with_show_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
            primary_outcomes=["outcome"],
            secondary_outcomes=["outcome"],
            segments=[],
        )

        url = reverse("nimbus-ui-update-metrics", kwargs={"slug": experiment.slug})
        response = self.client.get(f"{url}?show_errors=true")

        self.assertEqual(response.status_code, 200)
        validation_errors = response.context["validation_errors"]
        self.assertIn("primary_outcomes", validation_errors)
        self.assertIn("secondary_outcomes", validation_errors)

    def test_invalid_metrics_page_without_show_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
            primary_outcomes=["outcome"],
            secondary_outcomes=["outcome"],
            segments=[],
        )

        response = self.client.get(
            f"{reverse('nimbus-ui-update-metrics', kwargs={'slug': experiment.slug})}",
        )

        self.assertEqual(response.status_code, 200)
        validation_errors = response.context["validation_errors"]
        self.assertEqual(validation_errors, {})


class TestLaunchViews(AuthTestCase):
    def setUp(self):
        super().setUp()

        self.mock_preview_task = patch.object(
            nimbus_synchronize_preview_experiments_in_kinto, "apply_async"
        ).start()
        self.mock_push_task = patch.object(
            nimbus_check_kinto_push_queue_by_collection, "apply_async"
        ).start()
        self.mock_allocate_bucket_range = patch.object(
            NimbusExperiment, "allocate_bucket_range"
        ).start()
        self.mock_klaatu_task = patch.object(klaatu_start_job, "delay").start()

        self.addCleanup(patch.stopall)

    def test_draft_to_preview(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        response = self.client.post(
            reverse("nimbus-ui-draft-to-preview", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.PREVIEW)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.PREVIEW)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        self.mock_klaatu_task.assert_called_once_with(experiment_id=experiment.id)
        self.mock_preview_task.assert_called_once_with(countdown=5)
        self.mock_allocate_bucket_range.assert_called_once()

    def test_draft_to_review(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        response = self.client.post(
            reverse("nimbus-ui-draft-to-review", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

    def test_preview_to_review(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
            status_next=NimbusExperiment.Status.PREVIEW,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        response = self.client.post(
            reverse("nimbus-ui-preview-to-review", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

    def test_preview_to_draft(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
            status_next=NimbusExperiment.Status.PREVIEW,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        response = self.client.post(
            reverse("nimbus-ui-preview-to-draft", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        self.mock_preview_task.assert_called_once_with(countdown=5)

    def test_cancel_review(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )

        response = self.client.post(
            reverse("nimbus-ui-review-to-draft", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

    def test_review_to_approve_view(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )

        response = self.client.post(
            reverse("nimbus-ui-review-to-approve", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(f"{self.user.email} approved the review.", changelog.message)
        self.mock_push_task.assert_called_once_with(
            countdown=5, args=[experiment.kinto_collection]
        )
        self.mock_allocate_bucket_range.assert_called_once()

    def test_live_to_end_enrollment_view(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
        )

        response = self.client.post(
            reverse("nimbus-ui-live-to-end-enrollment", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)
        self.assertTrue(experiment.is_paused)

    @parameterized.expand(
        [
            (False,),
            (True,),
        ]
    )
    def test_live_to_complete_view(self, is_rollout):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
            is_rollout=is_rollout,
        )

        response = self.client.post(
            reverse("nimbus-ui-live-to-complete", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.COMPLETE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

    def test_approve_end_enrollment_view(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        response = self.client.post(
            reverse("nimbus-ui-approve-end-enrollment", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )
        self.assertTrue(experiment.is_paused)

    @parameterized.expand(
        [
            (False,),
            (True,),
        ]
    )
    def test_approve_end_experiment_view(self, is_rollout):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.COMPLETE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
            is_rollout=is_rollout,
        )

        response = self.client.post(
            reverse("nimbus-ui-approve-end-experiment", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.COMPLETE)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )
        self.assertTrue(experiment.is_paused)

    def test_reject_end_enrollment_view(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-cancel-end-enrollment",
                kwargs={"slug": experiment.slug},
            ),
            data={
                "changelog_message": "Enrollment should continue.",
                "action_type": "end_enrollment",
            },
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertFalse(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(
            "rejected the review with reason: Enrollment should continue.",
            changelog.message,
        )

    def test_cancel_end_enrollment_view(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-cancel-end-enrollment",
                kwargs={"slug": experiment.slug},
            ),
            data={
                "cancel_message": "Cancelled end enrollment request.",
                "action_type": "end_enrollment",
            },
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertFalse(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("Cancelled end enrollment request.", changelog.message)

    @parameterized.expand(
        [
            (False,),
            (True,),
        ]
    )
    def test_reject_end_experiment_view(self, is_rollout):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.COMPLETE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
            is_rollout=is_rollout,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-cancel-end-experiment",
                kwargs={"slug": experiment.slug},
            ),
            data={
                "changelog_message": "Experiment should continue.",
                "action_type": "end_experiment",
            },
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertTrue(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(
            "rejected the review with reason: Experiment should continue.",
            changelog.message,
        )

    @parameterized.expand(
        [
            (False,),
            (True,),
        ]
    )
    def test_cancel_end_experiment_view(self, is_rollout):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.COMPLETE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
            is_rollout=is_rollout,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-cancel-end-experiment",
                kwargs={"slug": experiment.slug},
            ),
            data={
                "cancel_message": "Cancelled end experiment request.",
                "action_type": "end_experiment",
            },
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertTrue(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("Cancelled end experiment request.", changelog.message)

    def test_live_to_update_rollout_view(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_rollout=True,
        )

        response = self.client.post(
            reverse("nimbus-ui-live-to-update-rollout", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

        changelog = experiment.changes.latest("changed_on")
        self.assertIn("requested review to update Audience", changelog.message)

    def test_cancel_update_rollout_view_with_rejection(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        response = self.client.post(
            reverse("nimbus-ui-cancel-update-rollout", kwargs={"slug": experiment.slug}),
            data={
                "changelog_message": "Update not required.",
                "action_type": "update_rollout",
            },
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertIn("Update not required.", changelog.message)

    def test_cancel_update_rollout_view_with_cancel_message(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        response = self.client.post(
            reverse("nimbus-ui-cancel-update-rollout", kwargs={"slug": experiment.slug}),
            data={
                "cancel_message": "Cancelled update rollout.",
                "action_type": "update_rollout",
            },
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertIn("Cancelled update rollout.", changelog.message)

    def test_approve_update_rollout_view(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        response = self.client.post(
            reverse("nimbus-ui-approve-update-rollout", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )

        changelog = experiment.changes.latest("changed_on")
        self.assertIn("approved the update review request", changelog.message)
        self.mock_push_task.assert_called_once_with(
            countdown=5, args=[experiment.kinto_collection]
        )
        self.mock_preview_task.assert_called_once_with(countdown=5)
        self.mock_allocate_bucket_range.assert_called_once()


class TestAudienceUpdateView(AuthTestCase):
    def test_get_draft_renders_page(self):
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment.required_experiments.add(required)
        experiment.excluded_experiments.add(excluded)

        response = self.client.get(
            reverse("nimbus-ui-update-audience", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_live_rollout_renders_page(self):
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
        )
        experiment.required_experiments.add(required)
        experiment.excluded_experiments.add(excluded)

        response = self.client.get(
            reverse("nimbus-ui-update-audience", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_get_non_draft_redirects_to_summary(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, is_rollout=False
        )
        response = self.client.get(
            reverse("nimbus-ui-update-audience", kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug})
        )

    @parameterized.expand(
        [
            (NimbusExperimentFactory.Lifecycles.PREVIEW,),
            (NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,),
            (NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,),
        ]
    )
    def test_post_non_draft_hx_redirects_to_summary(self, lifecycle):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle, is_rollout=False
        )
        response = self.client.post(
            reverse("nimbus-ui-update-audience", kwargs={"slug": experiment.slug}), {}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("HX-Redirect"),
            (
                f"{reverse('nimbus-ui-detail', kwargs={'slug': experiment.slug})}"
                "?save_failed=true"
            ),
        )

    def test_post_updates_overview(self):
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            total_enrolled_clients=0,
            is_sticky=False,
            countries=[],
            locales=[],
            languages=[],
            exclude_countries=False,
            exclude_locales=False,
            exclude_languages=False,
        )

        response = self.client.post(
            reverse("nimbus-ui-update-audience", kwargs={"slug": experiment.slug}),
            {
                "channel": NimbusExperiment.Channel.BETA,
                "countries": [country.id],
                "excluded_experiments_branches": [f"{excluded.slug}:None"],
                "exclude_countries": True,
                "exclude_locales": True,
                "exclude_languages": True,
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": True,
                "languages": [language.id],
                "locales": [locale.id],
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "required_experiments_branches": [f"{required.slug}:None"],
                "targeting_config_slug": (NimbusExperiment.TargetingConfig.FIRST_RUN),
                "total_enrolled_clients": 100,
            },
        )

        self.assertEqual(response.status_code, 200)
        experiment = NimbusExperiment.objects.get(slug=experiment.slug)

        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.channel, NimbusExperiment.Channel.BETA)
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.FIREFOX_83
        )
        self.assertEqual(
            experiment.firefox_max_version, NimbusExperiment.Version.FIREFOX_84
        )
        self.assertEqual(experiment.population_percent, 10)
        self.assertEqual(experiment.proposed_duration, 120)
        self.assertEqual(experiment.proposed_enrollment, 42)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusExperiment.TargetingConfig.FIRST_RUN,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])
        self.assertEqual(list(experiment.languages.all()), [language])
        self.assertTrue(experiment.exclude_countries)
        self.assertTrue(experiment.exclude_locales)
        self.assertTrue(experiment.exclude_languages)
        self.assertTrue(experiment.is_sticky)
        self.assertEqual(experiment.excluded_experiments.get(), excluded)
        self.assertTrue(
            NimbusExperimentBranchThroughExcluded.objects.filter(
                parent_experiment=experiment, child_experiment=excluded, branch_slug=None
            ).exists()
        )
        self.assertEqual(experiment.required_experiments.get(), required)
        self.assertTrue(
            NimbusExperimentBranchThroughRequired.objects.filter(
                parent_experiment=experiment, child_experiment=required, branch_slug=None
            ).exists()
        )

    def test_invalid_form_fields_with_show_errors(self):
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            total_enrolled_clients=0,
            is_sticky=False,
            countries=[],
            locales=[],
            languages=[],
        )
        base_url = reverse("nimbus-ui-update-audience", kwargs={"slug": experiment.slug})
        response = self.client.post(
            f"{base_url}?show_errors=true",
            {
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_97,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_96,
                "is_sticky": True,
                "population_percent": 0,
                "proposed_duration": 0,
                "proposed_enrollment": 0,
                "required_experiments_branches": [f"{required.slug}:None"],
                "total_enrolled_clients": 0,
            },
        )

        self.assertEqual(response.status_code, 200)

        validation_errors = response.context["validation_errors"]
        self.assertIn(
            "Ensure this value is greater than or equal to 1.",
            validation_errors["proposed_duration"],
        )
        self.assertIn(
            "Ensure this value is greater than or equal to 0.0001.",
            validation_errors["population_percent"],
        )
        self.assertIn(
            "Ensure this value is greater than or equal to 1.",
            validation_errors["proposed_enrollment"],
        )

    def test_invalid_form_fields_without_show_errors(self):
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            total_enrolled_clients=0,
            is_sticky=False,
            countries=[],
            locales=[],
            languages=[],
        )
        response = self.client.post(
            reverse("nimbus-ui-update-audience", kwargs={"slug": experiment.slug}),
            {
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_97,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_96,
                "is_sticky": True,
                "population_percent": 0,
                "proposed_duration": 0,
                "proposed_enrollment": 0,
                "required_experiments_branches": [f"{required.slug}:None"],
                "total_enrolled_clients": 0,
            },
        )

        self.assertEqual(response.status_code, 200)

        validation_errors = response.context["validation_errors"]
        self.assertEqual(validation_errors, {})

    def test_post_sets_rollout_dirty_on_population_change(self):
        experiment = NimbusExperimentFactory.create(
            is_rollout=True,
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            is_paused=False,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            population_percent=5,
            application=NimbusExperiment.Application.DESKTOP,
            channels=[NimbusExperiment.Channel.BETA],
        )

        response = self.client.post(
            reverse("nimbus-ui-update-audience", kwargs={"slug": experiment.slug}),
            {
                "channel": NimbusExperiment.Channel.BETA,
                "countries": [],
                "excluded_experiments_branches": [],
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": False,
                "languages": [],
                "locales": [],
                "population_percent": 10,
                "proposed_duration": 1,
                "proposed_enrollment": 1,
                "required_experiments_branches": [],
                "targeting_config_slug": NimbusExperiment.TargetingConfig.NO_TARGETING,
                "total_enrolled_clients": 0,
            },
        )

        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertTrue(experiment.is_rollout_dirty)


class TestSaveAndContinueMixin(AuthTestCase):
    @parameterized.expand(
        [
            (
                "nimbus-ui-update-overview",
                "nimbus-ui-update-branches",
                {
                    "name": "new name",
                    "documentation_links-TOTAL_FORMS": "0",
                    "documentation_links-INITIAL_FORMS": "0",
                },
            ),
            ("nimbus-ui-update-branches", "nimbus-ui-update-metrics", {}),
            ("nimbus-ui-update-metrics", "nimbus-ui-update-audience", {}),
            ("nimbus-ui-update-audience", "nimbus-ui-detail", {}),
        ]
    )
    def test_get_redirects_to_next_step(self, current_url, next_url, data):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        response = self.client.post(
            reverse(current_url, kwargs={"slug": experiment.slug}),
            {**data, "save_action": "continue"},
            headers={"Hx-Request": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse(next_url, kwargs={"slug": experiment.slug}),
        )


class TestResultsView(AuthTestCase):
    def test_render_to_response(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
        )

        response = self.client.get(
            reverse("nimbus-ui-results", kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["experiment"], experiment)
        self.assertTemplateUsed(response, "nimbus_experiments/results.html")


class TestBranchScreenshotCreateView(AuthTestCase):
    def test_post_creates_screenshot(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        branch = experiment.reference_branch
        branch.screenshots.all().delete()
        response = self.client.post(
            reverse(
                "nimbus-ui-create-branch-screenshot", kwargs={"slug": experiment.slug}
            ),
            {"branch_id": branch.id},
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(branch.screenshots.count(), 1)


class TestBranchScreenshotDeleteView(AuthTestCase):
    def test_post_deletes_screenshot(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        branch = experiment.reference_branch
        screenshot = branch.screenshots.create(description="To be deleted")
        response = self.client.post(
            reverse(
                "nimbus-ui-delete-branch-screenshot", kwargs={"slug": experiment.slug}
            ),
            {"screenshot_id": screenshot.id},
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertFalse(branch.screenshots.filter(id=screenshot.id).exists())


class TestNimbusExperimentsHomeView(AuthTestCase):
    def test_home_view_shows_owned_and_subscribed_experiments(self):
        # Owned by current user
        owned_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user, slug="owned-exp"
        )

        # Subscribed experiment
        other_user = UserFactory.create()
        subscribed_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            owner=other_user,
            slug="subscribed-exp",
        )
        subscribed_exp.subscribers.add(self.user)

        # Irrelevant
        unrelated_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING, slug="unrelated-exp"
        )

        response = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(response.status_code, 200)

        experiments = list(response.context["experiments"])

        self.assertIn(owned_exp, experiments)
        self.assertIn(subscribed_exp, experiments)
        self.assertNotIn(unrelated_exp, experiments)

        draft_or_preview_page = response.context["draft_or_preview_page"].object_list
        self.assertIn(owned_exp, draft_or_preview_page)
        self.assertIn(subscribed_exp, draft_or_preview_page)

    def test_home_view_filter_archived_experiments(self):
        non_archived_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user, slug="owned-exp"
        )
        archived_exp = NimbusExperimentFactory.create(is_archived=True, owner=self.user)
        response = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(response.status_code, 200)

        experiments = list(response.context["experiments"])
        self.assertIn(non_archived_exp, experiments)
        self.assertNotIn(archived_exp, experiments)

    def test_home_view_renders_template(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user
        )
        response = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nimbus_experiments/home.html")

    def test_draft_or_preview_context_pagination(self):
        draft = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user
        )
        preview = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW, owner=self.user
        )
        live = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING, owner=self.user
        )

        response = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(response.status_code, 200)
        draft_preview_page = response.context["draft_or_preview_page"].object_list
        self.assertIn(draft, draft_preview_page)
        self.assertIn(preview, draft_preview_page)
        self.assertNotIn(live, draft_preview_page)

    def test_draft_or_preview_pagination_respects_page_size(self):
        for _ in range(7):
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user
            )

        response = self.client.get(reverse("nimbus-ui-home") + "?draft_page=1")
        page = response.context["draft_or_preview_page"]
        self.assertEqual(page.number, 1)
        self.assertEqual(page.paginator.per_page, 5)
        self.assertEqual(len(page.object_list), 5)

        response = self.client.get(reverse("nimbus-ui-home") + "?draft_page=2")
        page2 = response.context["draft_or_preview_page"]
        self.assertEqual(page2.number, 2)
        self.assertEqual(len(page2.object_list), 2)

    def test_ready_for_attention_context_pagination(self):
        in_review = NimbusExperimentFactory.create(
            owner=self.user,
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            slug="review-exp",
        )
        missing_takeaways = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            owner=self.user,
            slug="missing-takeaways-exp",
            conclusion_recommendations=[],
            takeaways_summary="",
        )
        should_end_enrollment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            owner=self.user,
            proposed_enrollment=1,
            start_date=datetime.date.today() - datetime.timedelta(days=2),
            slug="end-enrollment-exp",
        )
        overdue_end = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            owner=self.user,
            proposed_duration=10,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            slug="overdue-exp",
        )
        complete_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            owner=self.user,
            slug="complete-exp",
            status=NimbusExperiment.Status.COMPLETE,
            conclusion_recommendations=["RERUN", "STOP"],
            takeaways_summary="",
        )
        complete_exp2 = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            owner=self.user,
            slug="complete-exp2",
            status=NimbusExperiment.Status.COMPLETE,
            takeaways_summary="takeaway",
        )
        draft_exp = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user, slug="draft-exp"
        )

        response = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(response.status_code, 200)

        attention_page = response.context["ready_for_attention_page"].object_list

        self.assertIn(in_review, attention_page)
        self.assertIn(missing_takeaways, attention_page)
        self.assertIn(should_end_enrollment, attention_page)
        self.assertIn(overdue_end, attention_page)
        self.assertNotIn(complete_exp, attention_page)
        self.assertNotIn(complete_exp2, attention_page)
        self.assertNotIn(draft_exp, attention_page)

    def test_all_my_experiments_context_pagination(self):
        owned = [
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.CREATED,
                owner=self.user,
                slug=f"owned-{i}",
            )
            for i in range(10)
        ]

        other_user = UserFactory.create()
        subscribed = [
            NimbusExperimentFactory.create_with_lifecycle(
                NimbusExperimentFactory.Lifecycles.PREVIEW,
                owner=other_user,
                slug=f"subscribed-{i}",
            )
            for i in range(10)
        ]
        for exp in subscribed:
            exp.subscribers.add(self.user)

        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING, slug="unrelated-exp"
        )

        response = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(response.status_code, 200)

        all_my_experiments_page = response.context["all_my_experiments_page"].object_list

        for exp in owned + subscribed:
            self.assertIn(exp, all_my_experiments_page)

        self.assertFalse(
            any(exp.slug == "unrelated-exp" for exp in all_my_experiments_page)
        )
        self.assertLessEqual(len(all_my_experiments_page), 25)

    def test_my_deliveries_filter_options_all_deliveries_default(self):
        owned = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user, slug="owned-exp"
        )
        other_user = UserFactory.create()
        subscribed = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            owner=other_user,
            slug="subscribed-exp",
        )
        subscribed.subscribers.add(self.user)
        unrelated = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="unrelated-exp",
        )
        response = self.client.get(reverse("nimbus-ui-home"))
        experiments = list(response.context["all_my_experiments_page"].object_list)
        self.assertIn(owned, experiments)
        self.assertIn(subscribed, experiments)
        self.assertNotIn(unrelated, experiments)

    def test_my_deliveries_filter_options_all_deliveries(self):
        owned = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user, slug="owned-exp"
        )
        other_user = UserFactory.create()
        subscribed = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            owner=other_user,
            slug="subscribed-exp",
        )
        subscribed.subscribers.add(self.user)
        unrelated = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="unrelated-exp",
        )
        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?my_deliveries_status={MyDeliveriesChoices.ALL}"
        )
        experiments = list(response.context["all_my_experiments_page"].object_list)
        self.assertIn(owned, experiments)
        self.assertIn(subscribed, experiments)
        self.assertNotIn(unrelated, experiments)

    def test_my_deliveries_filter_options_subscribed(self):
        other_user = UserFactory.create()
        subscribed = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            owner=other_user,
            slug="subscribed-exp",
        )
        subscribed.subscribers.add(self.user)

        unrelated = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="unrelated-exp",
        )

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?my_deliveries_status={MyDeliveriesChoices.SUBSCRIBED}"
        )
        experiments = list(response.context["all_my_experiments_page"].object_list)
        self.assertIn(subscribed, experiments)
        self.assertNotIn(unrelated, experiments)

    def test_my_deliveries_filter_options_owned(self):
        owned = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, owner=self.user, slug="owned-exp"
        )

        unrelated = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            slug="unrelated-exp",
        )
        response = response = self.client.get(
            f"{reverse('nimbus-ui-home')}?my_deliveries_status={MyDeliveriesChoices.OWNED}"
        )
        experiments = list(response.context["all_my_experiments_page"].object_list)
        self.assertIn(owned, experiments)
        self.assertNotIn(unrelated, experiments)

    def test_sorting_and_pagination_preserved(self):
        names = ["Charlie", "Alpha", "Foxtrot", "Bravo", "Echo", "Delta"]
        for name in names:
            NimbusExperimentFactory.create(owner=self.user, name=name)

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?sort=name&my_deliveries_page=1"
        )
        self.assertEqual(response.status_code, 200)
        page1_names = [
            e.name for e in response.context["all_my_experiments_page"].object_list
        ]
        self.assertEqual(page1_names, sorted(names)[:6])

    @parameterized.expand(
        [
            (
                {
                    "is_firefox_labs_opt_in": True,
                    "firefox_labs_title": "title",
                    "firefox_labs_description": "description",
                    "firefox_labs_group": (
                        NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING
                    ),
                },
                NimbusConstants.HomeTypeChoices.LABS.label,
            ),
            (
                {"is_rollout": True},
                NimbusConstants.HomeTypeChoices.ROLLOUT.label,
            ),
            (
                {},
                NimbusConstants.HomeTypeChoices.EXPERIMENT.label,
            ),
        ]
    )
    def test_home_type_display_returns_only_emoji(
        self, experiment_kwargs, expected_label
    ):
        experiment = NimbusExperimentFactory.create(owner=self.user, **experiment_kwargs)
        self.assertEqual(experiment.home_type_choice, expected_label)


class TestSlugRedirectToSummary(AuthTestCase):
    def test_slug_with_trailing_slash_redirects_to_summary(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        url = reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug}).replace(
            "summary/", ""
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug}),
        )

    def test_slug_without_trailing_slash_redirects_to_summary(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )
        url = reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug}).replace(
            "/summary/", ""
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug}),
        )


class TestNimbusFeaturesView(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.features = {
            "feature-desktop": NimbusExperiment.Application.DESKTOP,
            "feature-mobile": NimbusExperiment.Application.IOS,
            "feature-web": NimbusExperiment.Application.EXPERIMENTER,
        }
        self.feature_configs = {}
        for item, value in self.features.items():
            self.feature_configs[item] = NimbusFeatureConfigFactory.create(
                slug=item, name=item.replace("-", " "), application=value
            )

    def test_features_view_renders_template(self):
        response = self.client.get(reverse("nimbus-ui-features"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nimbus_experiments/features.html")

    def test_features_view_dropdown_loads_correct_default(self):
        response = self.client.get(reverse("nimbus-ui-features"))
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertTrue(form.fields["application"])
        self.assertEqual(form.fields["application"].initial, "")
        self.assertTrue(form.fields["feature_configs"])
        self.assertEqual(form.fields["feature_configs"].initial, "")

    @parameterized.expand(
        [
            (NimbusExperiment.Application.DESKTOP, "feature-desktop"),
            (NimbusExperiment.Application.IOS, "feature-mobile"),
            (NimbusExperiment.Application.EXPERIMENTER, "feature-web"),
        ]
    )
    def test_features_view_dropdown_loads_correct_fields_on_request(
        self, application, feature_config
    ):
        feature_id = NimbusFeatureConfig.objects.values_list("pk", flat=True).get(
            slug=feature_config
        )
        url = reverse("nimbus-ui-features")
        response = self.client.get(
            f"{url}?application={application.value}&feature_configs={feature_id}"
        )

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.fields["application"])
        self.assertEqual(form["application"].value(), application)
        self.assertEqual(form["feature_configs"].value(), str(feature_id))

    def test_features_view_multiapplication_loads_in_feature_config(self):
        applications = [
            NimbusExperiment.Application.DESKTOP,
            NimbusExperiment.Application.IOS,
        ]
        feature_config_multi = NimbusFeatureConfigFactory.create(
            slug="feature-multi",
            name="Multi Feature",
            application=applications,
        )

        url = reverse("nimbus-ui-features")
        response = self.client.get(
            f"{url}?application={applications[1].value}&feature_configs={feature_config_multi.id}"
        )

        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.fields["application"])
        self.assertEqual(form["application"].value(), applications[1].value)
        self.assertEqual(form["feature_configs"].value(), str(feature_config_multi.id))

    def test_features_view_pagination(self):
        application = NimbusExperiment.Application.DESKTOP
        for num in range(6):
            NimbusExperimentFactory.create(
                name=f"Experiment {num}",
                application=application,
                feature_configs=[self.feature_configs["feature-desktop"]],
                qa_status=NimbusExperiment.QAStatus.GREEN,
            )

        base_url = reverse("nimbus-ui-features")
        response = self.client.get(
            f"{base_url}?application={application.value}&feature_configs={self.feature_configs['feature-desktop'].id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["experiments_delivered"]), 5)
        self.assertEqual(len(response.context["experiments_with_qa_status"]), 5)

    @parameterized.expand(
        [
            (NimbusExperiment.Application.DESKTOP, "feature-desktop"),
            (NimbusExperiment.Application.IOS, "feature-mobile"),
            (NimbusExperiment.Application.EXPERIMENTER, "feature-web"),
        ]
    )
    def test_features_view_renders_table_with_correct_elements(
        self, application, feature_config
    ):
        experiment = f"Experiment {feature_config.replace('-', ' ')}"
        NimbusExperimentFactory.create(
            name=experiment,
            application=application,
            feature_configs=[self.feature_configs[feature_config]],
        )

        feature_id = self.feature_configs[feature_config].id
        url = reverse("nimbus-ui-features")
        response = self.client.get(
            f"{url}?application={application.value}&feature_configs={feature_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "deliveries-table")
        self.assertContains(response, "qa-info-table")
        self.assertContains(response, experiment)

    def test_features_view_deliveries_table_can_sort_by_recipe_name(self):
        experiment1 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            name="A Experiment",
        )
        experiment2 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            name="B Experiment",
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.NAME_UP,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.NAME_DOWN,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_features_view_deliveries_table_can_sort_by_qa_run_date(self):
        experiment1 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            qa_run_date=datetime.date(2024, 1, 1),
        )
        experiment2 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            qa_run_date=datetime.date(2024, 1, 2),
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.QARuns.DATE_UP,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.QARuns.DATE_DOWN,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_features_view_deliveries_table_can_sort_by_date(self):
        experiment1 = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            start_date=datetime.date(2024, 1, 1),
        )
        experiment2 = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle=NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            start_date=datetime.date(2024, 1, 2),
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.DATE_UP,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.DATE_DOWN,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_features_view_deliveries_table_can_sort_by_experiment_type(self):
        experiment1 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            is_rollout=False,
        )
        experiment2 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            is_rollout=True,
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.TYPE_UP,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.TYPE_DOWN,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_features_view_deliveries_table_can_sort_by_qa_run_type(self):
        experiment1 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            qa_run_type=NimbusExperiment.QATestType.FULL,
        )
        experiment2 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            qa_run_type=NimbusExperiment.QATestType.SMOKE,
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.QARuns.TYPE_UP,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.QARuns.TYPE_DOWN,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_features_view_deliveries_table_can_sort_by_experiment_channel(self):
        experiment1 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            status=NimbusExperiment.Status.LIVE,
            channels=[NimbusExperiment.Channel.BETA],
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )
        experiment2 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            status=NimbusExperiment.Status.LIVE,
            channels=[NimbusExperiment.Channel.RELEASE],
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.CHANNEL_UP,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.CHANNEL_DOWN,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_features_view_deliveries_table_can_sort_by_versions(self):
        experiment1 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            status=NimbusExperiment.Status.LIVE,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
        )
        experiment2 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            status=NimbusExperiment.Status.LIVE,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_101,
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.VERSIONS_UP,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.VERSIONS_DOWN,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment2.slug, experiment1.slug],
        )

    def test_features_view_deliveries_table_can_sort_by_total_clients(self):
        experiment1 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            total_enrolled_clients=1500,
        )
        experiment2 = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[self.feature_configs["feature-desktop"]],
            total_enrolled_clients=200000,
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.SIZE_UP,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment1.slug, experiment2.slug],
        )

        response = self.client.get(
            reverse("nimbus-ui-features"),
            {
                "sort": FeaturesPageSortChoices.Deliveries.SIZE_DOWN,
                "application": NimbusExperiment.Application.DESKTOP.value,
                "feature_configs": self.feature_configs["feature-desktop"].id,
            },
        )

        self.assertEqual(
            [e.slug for e in response.context["experiments_delivered"]],
            [experiment2.slug, experiment1.slug],
        )
