import datetime
import json
from decimal import Decimal
from unittest import mock
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone
from parameterized import parameterized

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.constants import (
    EXTERNAL_URLS,
    RISK_QUESTIONS,
    NimbusConstants,
)
from experimenter.experiments.models import (
    NimbusExperiment,
    NimbusRolloutPlanTemplate,
)
from experimenter.experiments.tests.factories import (
    TINY_PNG,
    NimbusBranchScreenshotFactory,
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusRolloutPhaseFactory,
    TagFactory,
)
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.nimbus_ui.new.forms import (
    NimbusExperimentCreateForm,
    NimbusExperimentSidebarCloneForm,
    RolloutAudienceForm,
    RolloutOverviewForm,
    RolloutQAStatusForm,
    RolloutRisksForm,
    RolloutSignoffForm,
)
from experimenter.nimbus_ui.new.views import RolloutSetupProgressMixin
from experimenter.openidc.tests.factories import UserFactory
from experimenter.targeting.constants import NimbusTargetingConfig


class AuthTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(email="user@example.com")
        self.client.defaults[settings.OPENIDC_EMAIL_HEADER] = self.user.email


class TestRolloutStatusUpdateViews(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.mock_preview_task = patch(
            "experimenter.nimbus_ui.new.forms."
            "nimbus_synchronize_preview_experiments_in_kinto.apply_async"
        ).start()
        self.mock_allocate_bucket_range = patch(
            "experimenter.experiments.models.NimbusExperiment.allocate_bucket_range"
        ).start()
        self.mock_kinto_push_queue = patch(
            "experimenter.nimbus_ui.new.forms."
            "nimbus_check_kinto_push_queue_by_collection.apply_async"
        ).start()
        self.mock_emoji_task = patch(
            "experimenter.slack.tasks.add_emoji_to_message_async.delay"
        ).start()
        self.mock_remove_emoji_task = patch(
            "experimenter.slack.tasks.remove_emoji_from_message_async.delay"
        ).start()
        self.invalid_fields_patcher = patch.object(
            NimbusExperiment, "get_invalid_fields_errors", return_value={}
        )
        self.mock_invalid_fields = self.invalid_fields_patcher.start()
        self.addCleanup(self.mock_preview_task.stop)
        self.addCleanup(self.mock_allocate_bucket_range.stop)
        self.addCleanup(self.mock_kinto_push_queue.stop)
        self.addCleanup(self.mock_emoji_task.stop)
        self.addCleanup(self.mock_remove_emoji_task.stop)
        self.addCleanup(self.invalid_fields_patcher.stop)

    @parameterized.expand(
        [
            # Draft -> Preview
            (
                "nimbus-ui-new-draft-to-preview-rollout",
                NimbusExperiment.Status.DRAFT,
                NimbusExperiment.Status.PREVIEW,
                None,
                NimbusExperiment.PublishStatus.IDLE,
            ),
            # Draft -> Review
            (
                "nimbus-ui-new-draft-to-review-rollout",
                NimbusExperiment.Status.DRAFT,
                NimbusExperiment.Status.DRAFT,
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.PublishStatus.REVIEW,
            ),
            # Preview -> Draft
            (
                "nimbus-ui-new-preview-to-draft-rollout",
                NimbusExperiment.Status.PREVIEW,
                NimbusExperiment.Status.DRAFT,
                None,
                NimbusExperiment.PublishStatus.IDLE,
            ),
            # Live -> Live
            (
                "nimbus-ui-new-advance-phase-review-rollout",
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.PublishStatus.REVIEW,
            ),
            # Live -> Disabled
            (
                "nimbus-ui-new-live-to-disabled-rollout",
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.Status.DISABLED,
                NimbusExperiment.PublishStatus.REVIEW,
            ),
            # Disabled -> Live
            (
                "nimbus-ui-new-disabled-to-live-rollout",
                NimbusExperiment.Status.DISABLED,
                NimbusExperiment.Status.DISABLED,
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.PublishStatus.REVIEW,
            ),
        ]
    )
    def test_valid_submission(
        self,
        url_name,
        initial_status,
        expected_status,
        expected_status_next,
        expected_publish_status,
    ):
        form_class = resolve(
            reverse(url_name, kwargs={"slug": "test"})
        ).func.view_class.form_class
        experiment = NimbusExperimentFactory.create(
            status=initial_status,
            status_next=form_class.required_status_next,
            publish_status=form_class.required_publish_status,
            is_rollout=True,
        )
        if url_name == "nimbus-ui-new-live-to-disabled-rollout":
            NimbusRolloutPhaseFactory.create(experiment=experiment)

        response = self.client.post(reverse(url_name, kwargs={"slug": experiment.slug}))

        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, expected_status)
        self.assertEqual(experiment.status_next, expected_status_next)
        self.assertEqual(experiment.publish_status, expected_publish_status)

    def test_htmx_transition_refreshes_page(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_rollout=True,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-new-draft-to-preview-rollout",
                kwargs={"slug": experiment.slug},
            ),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["HX-Refresh"], "true")

    def test_non_htmx_transition_renders_response(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_rollout=True,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-new-draft-to-preview-rollout",
                kwargs={"slug": experiment.slug},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Refresh", response.headers)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, NimbusExperiment.Status.PREVIEW)

    @parameterized.expand(
        [
            # Approve Draft -> Live review.
            (
                "nimbus-ui-new-draft-review-to-approve-rollout",
                NimbusExperiment.Status.DRAFT,
                NimbusExperiment.Status.LIVE,
                NimbusExperiment.PublishStatus.APPROVED,
            ),
            # Reject Draft -> Live review.
            (
                "nimbus-ui-new-draft-review-to-reject-rollout",
                NimbusExperiment.Status.DRAFT,
                None,
                NimbusExperiment.PublishStatus.IDLE,
            ),
        ]
    )
    def test_draft_review_submission(
        self,
        url_name,
        expected_status,
        expected_status_next,
        expected_publish_status,
    ):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        response = self.client.post(reverse(url_name, kwargs={"slug": experiment.slug}))

        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertEqual(experiment.status, expected_status)
        self.assertEqual(experiment.status_next, expected_status_next)
        self.assertEqual(experiment.publish_status, expected_publish_status)

    def test_invalid_rollout_cannot_request_launch(self):
        self.mock_invalid_fields.return_value = {
            "risk_brand": [NimbusConstants.ERROR_REQUIRED_QUESTION]
        }
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_rollout=True,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-new-draft-to-review-rollout",
                kwargs={"slug": experiment.slug},
            )
        )

        experiment.refresh_from_db()
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertIn(
            NimbusUIConstants.ERROR_INVALID_ROLLOUT_LAUNCH,
            response.context["update_status_form_errors"],
        )

    def test_htmx_progress_card_renders_fragment(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
            is_rollout=True,
        )

        response = self.client.get(
            reverse(
                "nimbus-ui-new-live-to-disabled-rollout",
                kwargs={"slug": experiment.slug},
            ),
            {"fragment": "progress_card"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nimbus_experiments/launch_controls_v2.html")

    def test_invalid_submission_adds_status_form_errors_to_context(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
            is_rollout=True,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-new-live-to-disabled-rollout",
                kwargs={"slug": experiment.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Cannot perform this action: experiment must be in state",
            response.context["update_status_form_errors"][0],
        )

    def test_launch_request_shows_cancel_action_to_requester(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )

        self.client.post(
            reverse(
                "nimbus-ui-new-draft-to-review-rollout",
                kwargs={"slug": experiment.slug},
            )
        )
        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertContains(response, 'id="rollout-review-cancel-btn"')
        self.assertContains(
            response,
            reverse(
                "nimbus-ui-new-draft-review-to-reject-rollout",
                kwargs={"slug": experiment.slug},
            ),
        )

    def test_duplicate_phase_resume_submission_creates_phase_and_requests_review(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DISABLED,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_rollout=True,
        )
        final_phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=25
        )
        experiment.rollout_phase = final_phase
        experiment.save()

        response = self.client.post(
            reverse(
                "nimbus-ui-new-disabled-to-live-duplicate-phase-rollout",
                kwargs={"slug": experiment.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        duplicated_phase = experiment.rollout_phases.last()
        self.assertEqual(experiment.rollout_phases.count(), 2)
        self.assertNotEqual(duplicated_phase, final_phase)
        self.assertEqual(
            duplicated_phase.population_percent, final_phase.population_percent
        )
        self.assertEqual(experiment.status, NimbusExperiment.Status.DISABLED)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

    def test_duplicate_phase_resume_submission_without_current_phase_is_invalid(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DISABLED,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_rollout=True,
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-new-disabled-to-live-duplicate-phase-rollout",
                kwargs={"slug": experiment.slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            NimbusUIConstants.ERROR_ROLLOUT_REENABLE_REQUIRES_CURRENT_PHASE,
            response.context["update_status_form_errors"],
        )
        experiment.refresh_from_db()
        self.assertEqual(experiment.rollout_phases.count(), 0)
        self.assertIsNone(experiment.status_next)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)


class NewViewTestMixin:
    def assertResponseUsesForm(self, response, form_class):
        self.assertIsInstance(response.context["form"], form_class)
        self.assertEqual(
            response.context["cancel_url"],
            reverse(
                "new-nimbus-ui-rollout-detail",
                kwargs={"slug": response.context["experiment"].slug},
            ),
        )

    def overview_data(self, experiment, documentation_link=None, **overrides):
        data = {
            "name": experiment.name,
            "hypothesis": experiment.hypothesis,
            "public_description": experiment.public_description,
            "application": experiment.application,
            "documentation_links-TOTAL_FORMS": "0",
            "documentation_links-INITIAL_FORMS": "0",
        }
        if documentation_link:
            data.update(
                {
                    "documentation_links-TOTAL_FORMS": "1",
                    "documentation_links-INITIAL_FORMS": "1",
                    "documentation_links-0-id": documentation_link.id,
                    "documentation_links-0-title": (
                        NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                    ),
                    "documentation_links-0-link": "https://www.example.com",
                }
            )
        data.update(overrides)
        return data

    def audience_data(
        self, application=NimbusExperiment.Application.DESKTOP, **overrides
    ):
        targeting_config_slugs = [
            targeting.slug
            for targeting in NimbusTargetingConfig.targeting_configs
            if application.name in targeting.application_choice_names
        ]
        data = {
            "channel": NimbusExperiment.Channel.BETA,
            "channels": [NimbusExperiment.Channel.BETA],
            "countries": [],
            "exclude_countries": False,
            "exclude_languages": False,
            "exclude_locales": False,
            "excluded_experiments_branches": [],
            "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
            "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
            "is_first_run": False,
            "is_sticky": False,
            "languages": [],
            "locales": [],
            "localizations": "",
            "required_experiments_branches": [],
            "targeting_config_slug": (
                targeting_config_slugs[0]
                if targeting_config_slugs
                else NimbusExperiment.TargetingConfig.NO_TARGETING
            ),
            "is_localized": False,
        }
        data.update(overrides)
        return data


class TestNimbusRolloutDetailView(AuthTestCase):
    @mock.patch.object(NimbusExperiment, "get_invalid_fields_errors", return_value={})
    def test_ready_rollout_shows_preview_and_launch_actions(self, _mock_errors):
        experiment = NimbusExperimentFactory.create(
            is_rollout=True,
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertContains(response, 'id="rollout-preview-btn"')
        self.assertContains(response, 'id="rollout-launch-btn"')
        self.assertContains(
            response,
            reverse(
                "nimbus-ui-new-draft-to-review-rollout",
                kwargs={"slug": experiment.slug},
            ),
        )

    def test_get_returns_new_rollout_detail_context(self):
        tag = TagFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/rollout_detail.html")
        self.assertEqual(response.context["experiment"], experiment)
        self.assertIsInstance(
            response.context["clone_form"], NimbusExperimentSidebarCloneForm
        )
        self.assertIsInstance(response.context["create_form"], NimbusExperimentCreateForm)
        self.assertIn(tag, response.context["all_tags"])
        self.assertTrue(response.context["sidebar_links"])

    def test_setup_progress_complete_when_review_valid(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
        )
        NimbusRolloutPhaseFactory.create(experiment=experiment, population_percent=10)

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.context["setup_completion_percent"], 100)
        self.assertEqual(response.context["setup_issues_count"], 0)
        self.assertEqual(response.context["setup_issues"], [])

    def test_setup_progress_reports_issue_when_no_rollout_phases(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
        )
        self.assertFalse(experiment.rollout_phases.exists())

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        schedule_issues = [
            issue
            for issue in response.context["setup_issues"]
            if issue["card_id"] == "schedule"
        ]
        self.assertEqual(len(schedule_issues), 1)
        self.assertEqual(
            schedule_issues[0]["messages"],
            [NimbusConstants.ERROR_ROLLOUT_NO_PHASES],
        )
        self.assertLess(response.context["setup_completion_percent"], 100)

    def test_setup_progress_reports_issue_when_first_phase_population_zero(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE,
            is_rollout=True,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
        )
        NimbusRolloutPhaseFactory.create(experiment=experiment, population_percent=0)
        NimbusRolloutPhaseFactory.create(experiment=experiment, population_percent=50)

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        schedule_issues = [
            issue
            for issue in response.context["setup_issues"]
            if issue["card_id"] == "schedule"
        ]
        self.assertEqual(len(schedule_issues), 1)
        self.assertEqual(
            schedule_issues[0]["messages"],
            [NimbusConstants.ERROR_ROLLOUT_FIRST_PHASE_ZERO],
        )
        self.assertLess(response.context["setup_completion_percent"], 100)

    def test_setup_progress_reports_issues_when_review_invalid(self):
        experiment = NimbusExperimentFactory.create(
            public_description="",
            hypothesis=NimbusExperiment.HYPOTHESIS_DEFAULT,
            feature_configs=[],
            is_rollout=True,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertLess(response.context["setup_completion_percent"], 100)
        self.assertGreater(response.context["setup_issues_count"], 0)
        self.assertEqual(
            response.context["setup_issues_count"],
            len(response.context["setup_issues"]),
        )
        for issue in response.context["setup_issues"]:
            self.assertIn("section", issue)
            self.assertIn("card_id", issue)
            self.assertIn("label", issue)
            self.assertTrue(issue["messages"])

    def test_setup_progress_advances_per_field_within_a_section(self):
        experiment = NimbusExperimentFactory.create(is_rollout=True)
        url = reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})

        with mock.patch.object(
            NimbusExperiment,
            "get_invalid_fields_errors",
            return_value={
                "risk_brand": ["This field may not be null."],
                "risk_revenue": ["This field may not be null."],
            },
        ):
            two_invalid = self.client.get(url).context["setup_completion_percent"]

        with mock.patch.object(
            NimbusExperiment,
            "get_invalid_fields_errors",
            return_value={"risk_brand": ["This field may not be null."]},
        ):
            one_invalid = self.client.get(url).context["setup_completion_percent"]

        total_tracked = len(
            {
                field
                for section in RolloutSetupProgressMixin.SETUP_SECTIONS.values()
                for field in section["fields"]
            }
        )
        self.assertEqual(two_invalid, round(100 * (total_tracked - 2) / total_tracked))
        self.assertEqual(one_invalid, round(100 * (total_tracked - 1) / total_tracked))
        self.assertGreater(one_invalid, two_invalid)

    def test_setup_progress_untracked_issue_does_not_lower_completion(self):
        experiment = NimbusExperimentFactory.create(is_rollout=True)
        url = reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})

        with mock.patch.object(
            NimbusExperiment,
            "get_invalid_fields_errors",
            return_value={
                "reference_branch": {"feature_values": ["Feature not supported."]}
            },
        ):
            context = self.client.get(url).context

        self.assertEqual(context["setup_issues_count"], 1)
        self.assertEqual(context["setup_completion_percent"], 100)

    def test_preview_card_hidden_when_not_in_preview(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(experiment.is_preview)
        self.assertNotContains(response, "Preview links & testing details")

    def test_preview_card_shown_when_in_preview(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            is_rollout=True,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(experiment.is_preview)
        self.assertContains(response, "Preview links & testing details")
        self.assertContains(response, "Rollout experience")
        self.assertContains(response, EXTERNAL_URLS["PREVIEW_LAUNCH_DOC"])

    def test_preview_card_lists_all_screenshots(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            is_rollout=True,
        )
        screenshot_1 = NimbusBranchScreenshotFactory.create(
            branch=experiment.reference_branch
        )
        screenshot_2 = NimbusBranchScreenshotFactory.create(
            branch=experiment.reference_branch
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, screenshot_1.image.url)
        self.assertContains(response, screenshot_2.image.url)

    @override_settings(SKIP_REVIEW_ACCESS_CONTROL_FOR_DEV_USER=True)
    def test_sidebar_shows_approve_control_for_dev_reviewer(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: settings.DEV_USER_EMAIL},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="rollout-review-approve-btn"')
        self.assertContains(
            response,
            reverse(
                "nimbus-ui-new-draft-review-to-approve-rollout",
                kwargs={"slug": experiment.slug},
            ),
        )

    def test_setup_issues_disable_phase_advance_but_not_disable_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_rollout=True,
        )
        current_phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=10
        )
        NimbusRolloutPhaseFactory.create(experiment=experiment, population_percent=20)
        experiment.rollout_phase = current_phase
        experiment.save()

        with mock.patch.object(
            NimbusExperiment,
            "get_invalid_fields_errors",
            return_value={"risk_brand": [NimbusConstants.ERROR_REQUIRED_QUESTION]},
        ):
            response = self.client.get(
                reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
            )

        content = response.content.decode()
        next_phase_button = content.split('id="rollout-next-phase-btn"', 1)[1].split(
            "</button>", 1
        )[0]
        disable_button = content.split('id="rollout-disable-btn"', 1)[1].split(
            "</button>", 1
        )[0]
        self.assertRegex(next_phase_button, r"\sdisabled(?:\s|>)")
        self.assertNotRegex(disable_button, r"\sdisabled(?:\s|>)")

    @override_settings(SKIP_REVIEW_ACCESS_CONTROL_FOR_DEV_USER=True)
    def test_setup_issues_disable_phase_advance_approval(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        with mock.patch.object(
            NimbusExperiment,
            "get_invalid_fields_errors",
            return_value={"risk_brand": [NimbusConstants.ERROR_REQUIRED_QUESTION]},
        ):
            response = self.client.get(
                reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug}),
                **{settings.OPENIDC_EMAIL_HEADER: settings.DEV_USER_EMAIL},
            )

        content = response.content.decode()
        approve_button = content.split('id="rollout-review-approve-btn"', 1)[1].split(
            "</button>", 1
        )[0]
        self.assertRegex(approve_button, r"\sdisabled(?:\s|>)")

    @override_settings(SKIP_REVIEW_ACCESS_CONTROL_FOR_DEV_USER=True)
    def test_sidebar_shows_remote_settings_link_when_approved(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
            is_rollout=True,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: settings.DEV_USER_EMAIL},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Open Remote Settings")

    def test_get_returns_404_for_experiment(self):
        experiment = NimbusExperimentFactory.create(is_rollout=False)

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 404)


class TestNewOverviewUpdateView(NewViewTestMixin, AuthTestCase):
    url_name = "nimbus-ui-new-update-overview"

    def test_get_returns_edit_form_for_draft(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/overview/edit_form.html")
        self.assertResponseUsesForm(response, RolloutOverviewForm)
        self.assertContains(response, "Public description")

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
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug}),
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
            reverse(self.url_name, kwargs={"slug": experiment.slug}), {}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("HX-Redirect"),
            (
                f"{reverse('nimbus-ui-detail', kwargs={'slug': experiment.slug})}"
                "?save_failed=true"
            ),
        )

    def test_post_valid_saves_and_returns_display_card(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            self.overview_data(
                experiment,
                documentation_link,
                name="updated name",
                hypothesis="updated hypothesis",
                public_description="updated description",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/overview/card.html")
        experiment.refresh_from_db()
        self.assertEqual(experiment.name, "updated name")
        self.assertEqual(experiment.hypothesis, "updated hypothesis")
        self.assertEqual(experiment.public_description, "updated description")
        self.assertTrue(response.context["hx_swap_oob"])

    def test_post_invalid_returns_edit_form_with_errors(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "name": "",
                "documentation_links-TOTAL_FORMS": "0",
                "documentation_links-INITIAL_FORMS": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/overview/edit_form.html")
        self.assertTrue(response.context["form"].errors)
        self.assertTrue(response.context["hx_swap_oob"])
        self.assertContains(response, 'id="sidebar-setup-progress"')
        self.assertContains(response, 'hx-swap-oob="true"')


class TestNewRisksUpdateView(NewViewTestMixin, AuthTestCase):
    url_name = "nimbus-ui-new-update-risks"

    def test_get_returns_edit_form_for_draft(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/risks/edit_form.html")
        self.assertResponseUsesForm(response, RolloutRisksForm)
        self.assertContains(response, RISK_QUESTIONS["AI"])

    def test_post_valid_saves_and_returns_display_card(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            risk_ai=False,
            risk_brand=False,
            risk_message=False,
            risk_revenue=False,
            risk_partner_related=False,
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "risk_ai": True,
                "risk_brand": True,
                "risk_message": True,
                "risk_revenue": True,
                "risk_partner_related": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/risks/card.html")
        experiment.refresh_from_db()
        self.assertTrue(experiment.risk_ai)
        self.assertTrue(experiment.risk_brand)
        self.assertTrue(experiment.risk_message)
        self.assertTrue(experiment.risk_revenue)
        self.assertTrue(experiment.risk_partner_related)


class TestNewAudienceUpdateView(NewViewTestMixin, AuthTestCase):
    url_name = "nimbus-ui-new-update-audience"

    def test_get_returns_edit_form_for_draft(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/audience/edit_form.html")
        self.assertResponseUsesForm(response, RolloutAudienceForm)

    def test_post_valid_saves_and_returns_display_card(self):
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            countries=[],
            locales=[],
            languages=[],
            is_sticky=False,
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            self.audience_data(
                countries=[country.id],
                exclude_countries=True,
                languages=[language.id],
                locales=[locale.id],
                is_sticky=True,
                targeting_config_slug=NimbusExperiment.TargetingConfig.FIRST_RUN,
                save="True",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/audience/card.html")
        experiment.refresh_from_db()
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])
        self.assertEqual(list(experiment.languages.all()), [language])
        self.assertTrue(experiment.exclude_countries)
        self.assertTrue(experiment.is_sticky)
        self.assertEqual(
            experiment.targeting_config_slug, NimbusExperiment.TargetingConfig.FIRST_RUN
        )

    def test_get_renders_is_localized_checkbox(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Is this a localized rollout?")
        self.assertContains(response, 'id="id_is_localized"')

    def test_post_toggling_is_localized_saves_and_returns_edit_form(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            is_localized=False,
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            self.audience_data(is_localized=True),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/audience/edit_form.html")
        experiment.refresh_from_db()
        self.assertTrue(experiment.is_localized)
        self.assertContains(response, "Localization Substitutions")

    def test_post_save_persists_localization_fields_and_returns_card(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            is_localized=False,
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            self.audience_data(
                is_localized=True,
                localizations='{"en-US": {}}',
                save="True",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/audience/card.html")
        experiment.refresh_from_db()
        self.assertTrue(experiment.is_localized)
        self.assertEqual(experiment.localizations, '{"en-US": {}}')


class TestNewRolloutFeaturesUpdateView(AuthTestCase):
    url_name = "nimbus-ui-new-update-rollout-features"

    def test_post_valid_saves_and_returns_display_card(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            feature_configs=[],
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_experience": "Updated rollout experience",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "rollout-screenshots-TOTAL_FORMS": "0",
                "rollout-screenshots-INITIAL_FORMS": "0",
                "save": "True",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/rollout_features/card.html")
        experiment.refresh_from_db()
        self.assertEqual(experiment.takeaways_summary, "Updated rollout experience")
        self.assertTrue(response.context["hx_swap_oob"])

    def test_post_change_returns_edit_form(self):
        feature_config = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            slug="rollout-feature",
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[],
            takeaways_summary="Original rollout experience",
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_experience": "Updated rollout experience",
                "feature_configs": [feature_config.id],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "rollout-screenshots-TOTAL_FORMS": "0",
                "rollout-screenshots-INITIAL_FORMS": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/rollout_features/edit_form.html")
        self.assertContains(response, "rollout-feature")
        self.assertContains(response, "value-editor")
        experiment.refresh_from_db()
        self.assertEqual(experiment.takeaways_summary, "Original rollout experience")
        self.assertEqual(experiment.feature_configs.count(), 0)


class TestNewRolloutScreenshotCreateView(AuthTestCase):
    url_name = "nimbus-ui-new-create-rollout-screenshot"

    def test_post_creates_screenshot_and_returns_edit_form(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            feature_configs=[],
        )
        experiment.reference_branch.screenshots.all().delete()

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_experience": "",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "rollout-screenshots-TOTAL_FORMS": "0",
                "rollout-screenshots-INITIAL_FORMS": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/rollout_features/edit_form.html")
        self.assertEqual(experiment.reference_branch.screenshots.count(), 1)
        self.assertTrue(response.context["hx_swap_oob"])
        self.assertContains(response, 'id="sidebar-setup-progress"')
        self.assertContains(response, 'hx-swap-oob="true"')

    @mock.patch.object(NimbusExperiment, "get_invalid_fields_errors", return_value={})
    def test_post_saves_form_state_and_refreshes_actions_before_preview(
        self, _mock_errors
    ):
        experiment = NimbusExperimentFactory.create(
            is_rollout=True,
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            feature_configs=[],
            takeaways_summary="Original rollout experience",
        )
        experiment.reference_branch.screenshots.all().delete()

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_experience": "Updated without explicit save",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "rollout-screenshots-TOTAL_FORMS": "0",
                "rollout-screenshots-INITIAL_FORMS": "0",
            },
        )

        experiment.refresh_from_db()
        self.assertEqual(experiment.takeaways_summary, "Updated without explicit save")
        self.assertContains(response, 'id="rollout-preview-btn"')
        self.assertContains(response, 'id="rollout-launch-btn"')

        with (
            mock.patch.object(NimbusExperiment, "allocate_bucket_range"),
            mock.patch(
                "experimenter.nimbus_ui.new.forms."
                "nimbus_synchronize_preview_experiments_in_kinto.apply_async"
            ),
        ):
            self.client.post(
                reverse(
                    "nimbus-ui-new-draft-to-preview-rollout",
                    kwargs={"slug": experiment.slug},
                )
            )
        experiment.refresh_from_db()
        self.assertTrue(experiment.is_preview)


class TestNewRolloutScreenshotUploadView(AuthTestCase):
    url_name = "nimbus-ui-new-upload-rollout-screenshot"

    def test_post_saves_uploaded_image_and_returns_edit_form(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            feature_configs=[],
        )
        experiment.reference_branch.screenshots.all().delete()
        screenshot = experiment.reference_branch.screenshots.create()
        self.assertFalse(screenshot.image)

        image = SimpleUploadedFile(
            name="screenshot.png", content=TINY_PNG, content_type="image/png"
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_experience": "",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "rollout-screenshots-TOTAL_FORMS": "1",
                "rollout-screenshots-INITIAL_FORMS": "1",
                "rollout-screenshots-0-id": screenshot.id,
                "rollout-screenshots-0-description": "",
                "rollout-screenshots-0-image": image,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/rollout_features/edit_form.html")
        screenshot.refresh_from_db()
        self.assertTrue(screenshot.image)


class TestNewRolloutScreenshotDeleteView(AuthTestCase):
    url_name = "nimbus-ui-new-delete-rollout-screenshot"

    def test_post_deletes_image_and_returns_edit_form(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            feature_configs=[],
        )
        experiment.reference_branch.screenshots.all().delete()
        screenshot = NimbusBranchScreenshotFactory.create(
            branch=experiment.reference_branch
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "screenshot_id": screenshot.id,
                "rollout_experience": "",
                "feature_configs": [],
                "branch-feature-value-TOTAL_FORMS": "0",
                "branch-feature-value-INITIAL_FORMS": "0",
                "rollout-screenshots-TOTAL_FORMS": "1",
                "rollout-screenshots-INITIAL_FORMS": "1",
                "rollout-screenshots-0-id": screenshot.id,
                "rollout-screenshots-0-description": screenshot.description,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/rollout_features/edit_form.html")
        self.assertEqual(experiment.reference_branch.screenshots.count(), 0)


class TestNewQAUpdateView(NewViewTestMixin, AuthTestCase):
    url_name = "nimbus-ui-new-update-qa"

    def test_get_returns_edit_form_for_draft(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/qa/edit_form.html")
        self.assertResponseUsesForm(response, RolloutQAStatusForm)

    def test_post_valid_saves_and_returns_display_card(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            qa_status=NimbusExperiment.QAStatus.NOT_SET,
            qa_comment="",
            qa_run_test_plan_url="",
            qa_run_testrail_url="",
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "qa_status": NimbusExperiment.QAStatus.SELF_GREEN,
                "qa_comment": "QA testing completed",
                "qa_run_test_plan_url": "https://www.example.com/test-plan",
                "qa_run_testrail_url": "https://www.example.com/testrail",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/qa/card.html")
        experiment.refresh_from_db()
        self.assertEqual(experiment.qa_status, NimbusExperiment.QAStatus.SELF_GREEN)
        self.assertEqual(experiment.qa_comment, "QA testing completed")
        self.assertEqual(
            experiment.qa_run_test_plan_url, "https://www.example.com/test-plan"
        )
        self.assertEqual(
            experiment.qa_run_testrail_url, "https://www.example.com/testrail"
        )


class TestNewSignoffUpdateView(NewViewTestMixin, AuthTestCase):
    url_name = "nimbus-ui-new-update-signoff"

    def test_get_returns_edit_form_for_draft(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/signoff/edit_form.html")
        self.assertResponseUsesForm(response, RolloutSignoffForm)

    def test_post_valid_saves_and_returns_display_card(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            qa_signoff=False,
            vp_signoff=False,
            legal_signoff=False,
        )

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "qa_signoff": "on",
                "vp_signoff": "on",
                "legal_signoff": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/signoff/card.html")
        experiment.refresh_from_db()
        self.assertTrue(experiment.qa_signoff)
        self.assertTrue(experiment.vp_signoff)
        self.assertTrue(experiment.legal_signoff)


class TestNewDocumentationLinkCreateView(AuthTestCase):
    url_name = "nimbus-ui-new-create-documentation-link"

    def test_post_creates_link_and_returns_edit_form(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[],
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "name": experiment.name,
                "hypothesis": experiment.hypothesis,
                "application": experiment.application,
                "risk_brand": True,
                "risk_message": True,
                "public_description": experiment.public_description,
                "risk_revenue": True,
                "risk_partner_related": True,
                "documentation_links-TOTAL_FORMS": "0",
                "documentation_links-INITIAL_FORMS": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/overview/edit_form.html")
        self.assertEqual(experiment.documentation_links.count(), 1)

    def test_post_invalid_does_not_create_link(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[],
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "documentation_links-TOTAL_FORMS": "0",
                "documentation_links-INITIAL_FORMS": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/overview/edit_form.html")
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(experiment.documentation_links.count(), 0)


class TestNewDocumentationLinkDeleteView(AuthTestCase):
    url_name = "nimbus-ui-new-delete-documentation-link"

    def test_post_deletes_link_and_returns_edit_form(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "name": experiment.name,
                "hypothesis": experiment.hypothesis,
                "application": experiment.application,
                "risk_brand": True,
                "risk_message": True,
                "public_description": experiment.public_description,
                "risk_revenue": True,
                "risk_partner_related": True,
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
        self.assertTemplateUsed(response, "new/rollouts/overview/edit_form.html")
        self.assertEqual(experiment.documentation_links.count(), 0)

    def test_post_deletes_link_even_when_form_invalid(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "documentation_links-TOTAL_FORMS": "0",
                "documentation_links-INITIAL_FORMS": "0",
                "link_id": documentation_link.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/overview/edit_form.html")
        self.assertEqual(experiment.documentation_links.count(), 0)

    def test_post_locked_experiment_redirects(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            documentation_links=[documentation_link],
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {"link_id": documentation_link.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("HX-Redirect"),
            (
                f"{reverse('nimbus-ui-detail', kwargs={'slug': experiment.slug})}"
                "?save_failed=true"
            ),
        )
        self.assertEqual(experiment.documentation_links.count(), 1)


class TestNewOverviewCancelView(AuthTestCase):
    url_name = "nimbus-ui-new-cancel-overview"

    def test_post_discards_blank_links_and_returns_card(self):
        blank_link = NimbusDocumentationLinkFactory.create(link="")
        filled_link = NimbusDocumentationLinkFactory.create(
            link="https://www.example.com"
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[blank_link, filled_link],
            is_rollout=True,
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/overview/card.html")
        self.assertTrue(response.context["hx_swap_oob"])
        self.assertContains(response, 'id="sidebar-setup-progress"')
        self.assertContains(response, 'hx-swap-oob="true"')
        links = list(experiment.documentation_links.all())
        self.assertNotIn(blank_link, links)
        self.assertIn(filled_link, links)


class TestNewTagSearchView(AuthTestCase):
    def test_get_returns_matching_unassigned_tags(self):
        experiment = NimbusExperimentFactory.create()
        tag1 = TagFactory.create(name="Alpha")
        TagFactory.create(name="Beta")
        experiment.tags.add(tag1)

        response = self.client.get(
            reverse("nimbus-ui-new-search-tags", kwargs={"slug": experiment.slug}),
            {"q": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beta")
        self.assertNotContains(response, "Alpha")

    def test_get_filters_by_query(self):
        experiment = NimbusExperimentFactory.create()
        TagFactory.create(name="Alpha")
        TagFactory.create(name="Beta")

        response = self.client.get(
            reverse("nimbus-ui-new-search-tags", kwargs={"slug": experiment.slug}),
            {"q": "alp"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertNotContains(response, "Beta")


class TestNewAddTagView(AuthTestCase):
    def test_post_adds_tag_to_experiment(self):
        experiment = NimbusExperimentFactory.create()
        tag = TagFactory.create(name="MyTag")

        response = self.client.post(
            reverse("nimbus-ui-new-add-tag", kwargs={"slug": experiment.slug}),
            {"tag_id": tag.id},
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertIn(tag, experiment.tags.all())


class TestNewRemoveTagView(AuthTestCase):
    def test_post_removes_tag_from_experiment(self):
        experiment = NimbusExperimentFactory.create()
        tag = TagFactory.create(name="MyTag")
        experiment.tags.add(tag)

        response = self.client.post(
            reverse("nimbus-ui-new-remove-tag", kwargs={"slug": experiment.slug}),
            {"tag_id": tag.id},
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertNotIn(tag, experiment.tags.all())


class TestNewSubscriberSearchView(AuthTestCase):
    def test_get_returns_matching_users(self):
        experiment = NimbusExperimentFactory.create()
        user = UserFactory.create(email="findme@example.com")

        response = self.client.get(
            reverse(
                "nimbus-ui-new-search-subscribers",
                kwargs={"slug": experiment.slug},
            ),
            {"q": "findme"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user.email)

    def test_get_excludes_already_subscribed(self):
        experiment = NimbusExperimentFactory.create()
        user = UserFactory.create(email="already@example.com")
        experiment.subscribers.add(user)

        response = self.client.get(
            reverse(
                "nimbus-ui-new-search-subscribers",
                kwargs={"slug": experiment.slug},
            ),
            {"q": "already"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, user.email)

    def test_get_returns_empty_when_no_query(self):
        experiment = NimbusExperimentFactory.create()

        response = self.client.get(
            reverse(
                "nimbus-ui-new-search-subscribers",
                kwargs={"slug": experiment.slug},
            ),
        )
        self.assertEqual(response.status_code, 200)


class TestNewAddSubscriberView(AuthTestCase):
    def test_post_adds_subscriber(self):
        experiment = NimbusExperimentFactory.create()
        user = UserFactory.create()

        response = self.client.post(
            reverse(
                "nimbus-ui-new-add-subscriber",
                kwargs={"slug": experiment.slug},
            ),
            {"user_id": user.id},
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertIn(user, experiment.subscribers.all())


class TestNewRemoveSubscriberView(AuthTestCase):
    def test_post_removes_subscriber(self):
        experiment = NimbusExperimentFactory.create()
        user = UserFactory.create()
        experiment.subscribers.add(user)

        response = self.client.post(
            reverse(
                "nimbus-ui-new-remove-subscriber",
                kwargs={"slug": experiment.slug},
            ),
            {"user_id": user.id},
        )
        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertNotIn(user, experiment.subscribers.all())


class TestNewRolloutScheduleUpdateView(AuthTestCase):
    url_name = "nimbus-ui-new-update-schedule"

    def test_get_returns_edit_form_for_draft(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")

    def test_get_editable_when_live_rollout(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_rollout=True,
        )
        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")

    def test_get_locked_when_not_draft_or_rolling_out(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.PREVIEW,
            is_rollout=True,
        )
        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("nimbus-ui-detail", kwargs={"slug": experiment.slug}),
        )

    def test_get_shows_builtin_plan(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )
        for name, phases in NimbusUIConstants.ROLLOUT_TEMPLATE_PLANS.items():
            self.assertContains(response, name)
            self.assertContains(response, NimbusRolloutPlanTemplate.summary(phases))

    def test_get_hides_save_plan_action_when_no_phases(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        self.assertFalse(experiment.rollout_phases.exists())
        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="new-rollout-plan-field"')

    def test_get_shows_save_plan_action_after_phase_added(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        NimbusRolloutPhaseFactory.create(experiment=experiment)
        response = self.client.get(
            reverse(self.url_name, kwargs={"slug": experiment.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="new-rollout-plan-field"')

    def test_post_valid_saves_and_returns_display_card(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        phase = NimbusRolloutPhaseFactory.create(experiment=experiment)
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "2",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-start_date": "2026-01-15",
                "rollout_phases-0-end_date": "2026-01-29",
                "rollout_phases-0-population_percent": "25",
                "rollout_advance_observations": "Test rollout advance observations",
                "rollout_pause_observations": "Test rollout pause observations",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/card.html")
        experiment.refresh_from_db()
        phase = experiment.rollout_phases.get()
        self.assertEqual(phase.start_date, datetime.date(2026, 1, 15))
        self.assertEqual(phase.end_date, datetime.date(2026, 1, 29))
        self.assertEqual(phase.population_percent, 25)
        self.assertEqual(
            experiment.rollout_advance_observations, "Test rollout advance observations"
        )
        self.assertEqual(
            experiment.rollout_pause_observations, "Test rollout pause observations"
        )
        self.assertTrue(response.context["hx_swap_oob"])

    def test_post_in_progress_phase_shows_progress(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_rollout=True,
        )

        today = timezone.now().date()
        start = today - datetime.timedelta(days=3)
        end = today + datetime.timedelta(days=4)
        phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment, start_date=start, end_date=end
        )
        experiment.rollout_phase = phase
        experiment.save()
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "1",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-start_date": start.isoformat(),
                "rollout_phases-0-end_date": end.isoformat(),
                "rollout_phases-0-population_percent": "50",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/card.html")
        self.assertContains(response, "3/7 days complete")

    def test_post_can_change_in_progress_phase_dates(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_rollout=True,
        )
        phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment,
            population_percent=50,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 15),
        )
        experiment.rollout_phase = phase
        experiment.save()
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "1",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-start_date": "2026-02-01",
                "rollout_phases-0-end_date": "2026-02-20",
                "rollout_phases-0-population_percent": "90",
            },
        )
        self.assertEqual(response.status_code, 200)
        phase.refresh_from_db()
        self.assertEqual(phase.start_date, datetime.date(2026, 2, 1))
        self.assertEqual(phase.end_date, datetime.date(2026, 2, 20))
        self.assertEqual(phase.population_percent, 50)


class TestNewRolloutPhaseCreateView(AuthTestCase):
    url_name = "nimbus-ui-new-create-rollout-phase"

    def test_post_adds_phase_row_and_persists(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "0",
                "rollout_phases-INITIAL_FORMS": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")
        self.assertEqual(response.context["form"].rollout_phases.total_form_count(), 1)
        self.assertEqual(experiment.rollout_phases.count(), 1)


class TestNewRolloutPhaseDeleteView(AuthTestCase):
    url_name = "nimbus-ui-new-delete-rollout-phase"

    def test_post_removes_phase_row_and_persists(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        phase = NimbusRolloutPhaseFactory.create(experiment=experiment)
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "1",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-start_date": "2026-01-15",
                "rollout_phases-0-end_date": "2026-01-29",
                "rollout_phases-0-population_percent": "25",
                "phase_id": str(phase.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")
        self.assertEqual(response.context["form"].rollout_phases.total_form_count(), 0)
        self.assertEqual(experiment.rollout_phases.count(), 0)

    def test_post_does_not_delete_locked_phase(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_rollout=True,
        )
        done = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=10
        )
        current = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=50
        )
        experiment.rollout_phase = current
        experiment.save()
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "2",
                "rollout_phases-INITIAL_FORMS": "2",
                "rollout_phases-0-id": done.id,
                "rollout_phases-0-population_percent": "10",
                "rollout_phases-1-id": current.id,
                "rollout_phases-1-population_percent": "50",
                "phase_id": str(done.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(experiment.rollout_phases.filter(id=done.id).exists())

    def test_post_deletes_phase_when_another_phase_has_invalid_dates(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        invalid = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=10
        )
        target = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=50
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "2",
                "rollout_phases-INITIAL_FORMS": "2",
                "rollout_phases-0-id": invalid.id,
                "rollout_phases-0-start_date": "2026-01-15",
                "rollout_phases-0-end_date": "2026-01-01",
                "rollout_phases-0-population_percent": "10",
                "rollout_phases-1-id": target.id,
                "rollout_phases-1-population_percent": "50",
                "phase_id": str(target.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")
        self.assertFalse(experiment.rollout_phases.filter(id=target.id).exists())
        self.assertTrue(experiment.rollout_phases.filter(id=invalid.id).exists())

    def test_post_without_phase_id_deletes_nothing(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=10
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "1",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-population_percent": "10",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")
        self.assertTrue(experiment.rollout_phases.filter(id=phase.id).exists())


class TestNewRolloutPlanApplyView(AuthTestCase):
    url_name = "nimbus-ui-new-apply-rollout-plan"

    def test_post_applies_plan_phases_and_persists(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )

        plan_name, plan_percentages = next(
            iter(NimbusUIConstants.ROLLOUT_TEMPLATE_PLANS.items())
        )
        phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=99
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "1",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-population_percent": "99",
                "rollout_plan": plan_name,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")
        self.assertEqual(
            list(experiment.rollout_phases.values_list("population_percent", flat=True)),
            [Decimal(pct) for pct in plan_percentages],
        )

    def test_post_no_plan_leaves_phases_unchanged(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=99
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "1",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-population_percent": "99",
                "rollout_plan": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(experiment.rollout_phases.count(), 1)

    def test_post_applies_plan_preserving_locked_phase_with_inconsistent_dates(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            is_rollout=True,
        )
        plan_name, plan_percentages = next(
            iter(NimbusUIConstants.ROLLOUT_TEMPLATE_PLANS.items())
        )
        done = NimbusRolloutPhaseFactory.create(
            experiment=experiment,
            population_percent=1,
            start_date=datetime.date(2026, 7, 5),
            end_date=datetime.date(2026, 7, 2),
            actual_start_date=datetime.date(2026, 7, 2),
        )
        current = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=10
        )
        experiment.rollout_phase = current
        experiment.save()

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "2",
                "rollout_phases-INITIAL_FORMS": "2",
                "rollout_phases-0-id": done.id,
                "rollout_phases-1-id": current.id,
                "rollout_plan": plan_name,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")
        percents = sorted(
            experiment.rollout_phases.values_list("population_percent", flat=True)
        )
        self.assertEqual(
            percents,
            sorted(
                [Decimal("1.0000"), Decimal("10.0000")]
                + [Decimal(pct) for pct in plan_percentages]
            ),
        )


class TestNewRolloutPlanCreateView(AuthTestCase):
    url_name = "nimbus-ui-new-create-rollout-plan"

    def test_post_saves_submitted_phases_as_template(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        phase1 = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=5
        )
        phase2 = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=25
        )
        plan_name = next(iter(NimbusUIConstants.ROLLOUT_TEMPLATE_PLANS))

        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "2",
                "rollout_phases-INITIAL_FORMS": "2",
                "rollout_phases-0-id": phase1.id,
                "rollout_phases-0-population_percent": "7",
                "rollout_phases-1-id": phase2.id,
                "rollout_phases-1-population_percent": "30",
                "rollout_plan": plan_name,
                "template_name": "My custom plan",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/rollouts/schedule/edit_form.html")

        template = NimbusRolloutPlanTemplate.objects.get(name="My custom plan")
        self.assertEqual(template.phases, [7.0, 30.0])
        self.assertContains(response, '<option value="My custom plan" selected>')
        self.assertNotContains(response, f'<option value="{plan_name}" selected>')

    def test_post_blank_name_creates_nothing(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "0",
                "rollout_phases-INITIAL_FORMS": "0",
                "template_name": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(NimbusRolloutPlanTemplate.objects.filter(name="").exists())

    def test_post_duplicate_name_is_rejected(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        plan_name = next(iter(NimbusUIConstants.ROLLOUT_TEMPLATE_PLANS))
        phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=10
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "1",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-population_percent": "10",
                "template_name": plan_name,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, NimbusUIConstants.ERROR_ROLLOUT_PLAN_NAME_DUPLICATE)
        self.assertFalse(
            NimbusRolloutPlanTemplate.objects.filter(name=plan_name).exists()
        )

    def test_post_blocked_by_phase_error_shows_message_and_keeps_name(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )
        phase = NimbusRolloutPhaseFactory.create(
            experiment=experiment, population_percent=10
        )
        response = self.client.post(
            reverse(self.url_name, kwargs={"slug": experiment.slug}),
            {
                "rollout_phases-TOTAL_FORMS": "1",
                "rollout_phases-INITIAL_FORMS": "1",
                "rollout_phases-0-id": phase.id,
                "rollout_phases-0-start_date": "2026-01-15",
                "rollout_phases-0-end_date": "2026-01-01",
                "rollout_phases-0-population_percent": "10",
                "template_name": "My plan",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, NimbusUIConstants.ERROR_ROLLOUT_PLAN_FIX_ERRORS)
        self.assertContains(response, "My plan")
        self.assertFalse(
            NimbusRolloutPlanTemplate.objects.filter(name="My plan").exists()
        )


class TestNewSubscribeView(AuthTestCase):
    def test_post_subscribes_current_user(self):
        experiment = NimbusExperimentFactory.create()

        response = self.client.post(
            reverse("nimbus-ui-new-subscribe", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/common/subscribe_bell.html")
        experiment.refresh_from_db()
        self.assertIn(self.user, experiment.subscribers.all())
        self.assertContains(
            response,
            reverse("nimbus-ui-new-unsubscribe", kwargs={"slug": experiment.slug}),
        )


class TestNewUnsubscribeView(AuthTestCase):
    def test_post_unsubscribes_current_user(self):
        experiment = NimbusExperimentFactory.create()
        experiment.subscribers.add(self.user)

        response = self.client.post(
            reverse("nimbus-ui-new-unsubscribe", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/common/subscribe_bell.html")
        experiment.refresh_from_db()
        self.assertNotIn(self.user, experiment.subscribers.all())
        self.assertContains(
            response,
            reverse("nimbus-ui-new-subscribe", kwargs={"slug": experiment.slug}),
        )


class TestNewCloneView(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create(
            slug="test-experiment",
            application="firefox-desktop",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_120,
        )

    def test_post_clones_experiment_and_redirects_to_new_detail(self):
        response = self.client.post(
            reverse("nimbus-ui-new-clone", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user, "name": "Test Experiment Copy"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["HX-Redirect"],
            reverse(
                "new-nimbus-ui-rollout-detail",
                kwargs={"slug": "test-experiment-copy"},
            ),
        )
        experiment = NimbusExperiment.objects.get(slug="test-experiment-copy")
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)
        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.FIREFOX_120
        )

    def test_form_invalid_renders_with_experiment_context(self):
        response = self.client.post(
            reverse("nimbus-ui-new-clone", kwargs={"slug": self.experiment.slug}),
            {"owner": self.user, "name": "$."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(response.context["experiment"], self.experiment)


class TestNewToggleArchiveView(AuthTestCase):
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
            reverse(
                "nimbus-ui-new-toggle-archive", kwargs={"slug": self.experiment.slug}
            ),
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
            reverse(
                "nimbus-ui-new-toggle-archive", kwargs={"slug": self.experiment.slug}
            ),
            {"owner": self.user},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Refresh"), "true")

        updated_experiment = NimbusExperiment.objects.get(slug=self.experiment.slug)
        self.assertFalse(updated_experiment.is_archived)

    def test_detail_page_renders_archive_button(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            is_rollout=True,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("nimbus-ui-new-toggle-archive", kwargs={"slug": experiment.slug}),
        )
        self.assertContains(response, "Archive")


class TestNewToggleReviewSlackNotificationsView(AuthTestCase):
    def test_detail_page_renders_toggle_checked(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            enable_review_slack_notifications=True,
            is_rollout=True,
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="enable_review_slack_notifications"')
        self.assertContains(
            response,
            reverse(
                "nimbus-ui-new-toggle-review-slack-notifications",
                kwargs={"slug": experiment.slug},
            ),
        )
        self.assertContains(response, "checked")

    def test_post_enables_slack_notifications(self):
        experiment = NimbusExperimentFactory.create(
            enable_review_slack_notifications=False
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-new-toggle-review-slack-notifications",
                kwargs={"slug": experiment.slug},
            ),
            {"enable_review_slack_notifications": "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "new/common/slack_notifications_toggle.html")
        experiment.refresh_from_db()
        self.assertTrue(experiment.enable_review_slack_notifications)

    def test_post_disables_slack_notifications(self):
        experiment = NimbusExperimentFactory.create(
            enable_review_slack_notifications=True
        )

        response = self.client.post(
            reverse(
                "nimbus-ui-new-toggle-review-slack-notifications",
                kwargs={"slug": experiment.slug},
            ),
            {},
        )

        self.assertEqual(response.status_code, 200)
        experiment.refresh_from_db()
        self.assertFalse(experiment.enable_review_slack_notifications)


class TestToastTriggers(AuthTestCase):
    def assertToastTriggered(self, response, toast_id):
        self.assertEqual(
            json.loads(response.headers["HX-Trigger"]),
            {"showToast": {"id": toast_id}},
        )
        self.assertIn(toast_id, NimbusUIConstants.TOASTS)

    def test_saving_a_card_triggers_the_saved_toast(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, is_rollout=True
        )

        response = self.client.post(
            reverse("nimbus-ui-new-update-signoff", kwargs={"slug": experiment.slug}),
            {"qa_signoff": "on", "vp_signoff": "on", "legal_signoff": "on"},
        )

        self.assertToastTriggered(response, NimbusUIConstants.TOAST_SAVED)

    def test_subscribing_and_unsubscribing_trigger_toasts(self):
        experiment = NimbusExperimentFactory.create()

        response = self.client.post(
            reverse("nimbus-ui-new-subscribe", kwargs={"slug": experiment.slug})
        )
        self.assertToastTriggered(response, NimbusUIConstants.TOAST_SUBSCRIBED)

        response = self.client.post(
            reverse("nimbus-ui-new-unsubscribe", kwargs={"slug": experiment.slug})
        )
        self.assertToastTriggered(response, NimbusUIConstants.TOAST_UNSUBSCRIBED)

    def test_toggling_slack_notifications_triggers_toasts(self):
        experiment = NimbusExperimentFactory.create()
        url = reverse(
            "nimbus-ui-new-toggle-review-slack-notifications",
            kwargs={"slug": experiment.slug},
        )

        response = self.client.post(url, {"enable_review_slack_notifications": "on"})
        self.assertToastTriggered(response, NimbusUIConstants.TOAST_SLACK_ENABLED)

        response = self.client.post(url, {})
        self.assertToastTriggered(response, NimbusUIConstants.TOAST_SLACK_DISABLED)

    def test_every_toast_id_has_markup_on_the_page(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, is_rollout=True
        )

        response = self.client.get(
            reverse("new-nimbus-ui-rollout-detail", kwargs={"slug": experiment.slug})
        )

        for toast_id in NimbusUIConstants.TOASTS:
            self.assertContains(response, f'<div id="{toast_id}"')
