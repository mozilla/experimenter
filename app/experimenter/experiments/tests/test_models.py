import datetime

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from experimenter.openidc.tests.factories import UserFactory
from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
)
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentChangeLogFactory,
    ExperimentCommentFactory,
)


class TestExperimentManager(TestCase):

    def test_queryset_annotated_with_latest_change(self):
        now = timezone.now()
        experiment1 = ExperimentFactory.create_with_variants()
        experiment2 = ExperimentFactory.create_with_variants()

        ExperimentChangeLogFactory.create(
            experiment=experiment1,
            old_status=None,
            new_status=Experiment.STATUS_DRAFT,
            changed_on=(now - datetime.timedelta(days=2)),
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment2,
            old_status=None,
            new_status=Experiment.STATUS_DRAFT,
            changed_on=(now - datetime.timedelta(days=1)),
        )

        self.assertEqual(
            list(Experiment.objects.order_by("-latest_change")),
            [experiment2, experiment1],
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment1,
            old_status=experiment1.status,
            new_status=Experiment.STATUS_REVIEW,
        )

        self.assertEqual(
            list(Experiment.objects.order_by("-latest_change")),
            [experiment1, experiment2],
        )


class TestExperimentModel(TestCase):

    def test_get_absolute_url(self):
        experiment = ExperimentFactory.create(slug="experiment-slug")
        self.assertEqual(
            experiment.get_absolute_url(), "/experiments/experiment-slug/"
        )

    def test_experiment_url(self):
        experiment = ExperimentFactory.create(slug="experiment-slug")
        self.assertEqual(
            experiment.experiment_url,
            f"https://{settings.HOSTNAME}/experiments/experiment-slug/",
        )

    def test_accept_url(self):
        experiment = ExperimentFactory.create(slug="experiment")
        self.assertEqual(
            experiment.accept_url,
            f"https://{settings.HOSTNAME}"
            "/api/v1/experiments/experiment/accept/",
        )

    def test_reject_url(self):
        experiment = ExperimentFactory.create(slug="experiment")
        self.assertEqual(
            experiment.reject_url,
            f"https://{settings.HOSTNAME}"
            "/api/v1/experiments/experiment/reject/",
        )

    def test_bugzilla_url_returns_none_if_bugzilla_id_not_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        self.assertIsNone(experiment.bugzilla_url)

    def test_bugzilla_url_returns_url_when_bugzilla_id_is_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, bugzilla_id="1234"
        )
        self.assertEqual(
            experiment.bugzilla_url,
            settings.BUGZILLA_DETAIL_URL.format(id=experiment.bugzilla_id),
        )

    def test_test_tube_url_is_none_when_experiment_not_begun(self):
        experiment = ExperimentFactory.create(
            slug="experiment", status=Experiment.STATUS_DRAFT
        )
        self.assertIsNone(experiment.test_tube_url)

    def test_test_tube_url_is_none_when_experiment_is_addon_and_begun(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ADDON,
            slug="experiment",
            status=Experiment.STATUS_LIVE,
        )
        self.assertIsNone(experiment.test_tube_url)

    def test_test_tube_url_returns_url_when_experiment_is_pref_and_begun(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            slug="experiment",
            status=Experiment.STATUS_LIVE,
        )
        self.assertEqual(
            experiment.test_tube_url,
            "https://firefox-test-tube.herokuapp.com/experiments/experiment/",
        )

    def test_has_external_urls_is_false_when_no_external_urls(self):
        experiment = ExperimentFactory.create(
            data_science_bugzilla_url="", feature_bugzilla_url=""
        )
        self.assertFalse(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_data_science_bugzilla_url_is_set(
        self
    ):
        experiment = ExperimentFactory.create(
            data_science_bugzilla_url="www.bugzilla.com/123/"
        )
        self.assertTrue(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_feature_bugzilla_url_is_set(self):
        experiment = ExperimentFactory.create(
            feature_bugzilla_url="www.bugzilla.com/123/"
        )
        self.assertTrue(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_bugzilla_url_is_set(self):
        experiment = ExperimentFactory.create(bugzilla_id="1234")
        self.assertTrue(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_test_tube_url_is_set(self):
        experiment = ExperimentFactory.create(status=Experiment.STATUS_LIVE)
        self.assertTrue(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_bugzilla_and_test_tube_urls(self):
        experiment = ExperimentFactory.create(
            status=Experiment.STATUS_LIVE, bugzilla_id="1234"
        )
        self.assertTrue(experiment.has_external_urls)

    def test_start_date_returns_proposed_start_date_if_change_is_missing(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertEqual(experiment.start_date, experiment.proposed_start_date)

    def test_start_date_returns_datetime_if_change_exists(self):
        change = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_ACCEPTED,
            new_status=Experiment.STATUS_LIVE,
        )
        self.assertEqual(
            change.experiment.start_date, change.changed_on.date()
        )

    def test_observation_duration_returns_duration_minus_enrollment(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_duration=20, proposed_enrollment=10
        )
        self.assertEqual(experiment.observation_duration, 10)

    def test_observation_duration_returns_0_if_no_enrollment(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_duration=20, proposed_enrollment=None
        )
        self.assertEqual(experiment.observation_duration, 0)

    def test_compute_end_date_accepts_None_start_date(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=None
        )
        self.assertEqual(experiment._compute_end_date(1), None)

    def test_compute_end_date_accepts_None_duration(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1)
        )
        self.assertEqual(experiment._compute_end_date(None), None)

    def test_compute_end_date_accepts_valid_duration(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1)
        )
        self.assertEqual(
            experiment._compute_end_date(10), datetime.date(2019, 1, 11)
        )

    def test_compute_end_date_accepts_invalid_duration(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1)
        )
        self.assertEqual(
            experiment._compute_end_date(experiment.MAX_DURATION + 1), None
        )

    def test_end_date_uses_duration(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1),
            proposed_duration=20,
            proposed_enrollment=10,
        )
        self.assertEqual(experiment.end_date, datetime.date(2019, 1, 21))

    def test_enrollment_end_date_uses_enrollment_duration(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1),
            proposed_duration=20,
            proposed_enrollment=10,
        )
        self.assertEqual(experiment.end_date, datetime.date(2019, 1, 21))

    def test_format_date_string_accepts_none_for_start(self):
        experiment = ExperimentFactory.create_with_variants()
        output = experiment._format_date_string(
            None, datetime.date(2019, 1, 1)
        )
        self.assertEqual(output, "Unknown - Jan 01, 2019 (Unknown days)")

    def test_format_date_string_accepts_none_for_end(self):
        experiment = ExperimentFactory.create_with_variants()
        output = experiment._format_date_string(
            datetime.date(2019, 1, 1), None
        )
        self.assertEqual(output, "Jan 01, 2019 - Unknown (Unknown days)")

    def test_form_date_string_accepts_valid_start_end_dates(self):
        experiment = ExperimentFactory.create_with_variants()
        output = experiment._format_date_string(
            datetime.date(2019, 1, 1), datetime.date(2019, 1, 10)
        )
        self.assertEqual(output, "Jan 01, 2019 - Jan 10, 2019 (9 days)")

    def test_form_date_string_says_day_if_duration_is_1(self):
        experiment = ExperimentFactory.create_with_variants()
        output = experiment._format_date_string(
            datetime.date(2019, 1, 1), datetime.date(2019, 1, 2)
        )
        self.assertEqual(output, "Jan 01, 2019 - Jan 02, 2019 (1 day)")

    def test_dates_returns_date_string(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1), proposed_duration=20
        )
        self.assertEqual(
            experiment.dates, "Jan 01, 2019 - Jan 21, 2019 (20 days)"
        )

    def test_enrollment_dates_returns_date_string(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1),
            proposed_duration=20,
            proposed_enrollment=10,
        )
        self.assertEqual(
            experiment.enrollment_dates,
            "Jan 01, 2019 - Jan 11, 2019 (10 days)",
        )

    def test_observation_dates_returns_date_string(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1),
            proposed_duration=20,
            proposed_enrollment=10,
        )
        self.assertEqual(
            experiment.observation_dates,
            "Jan 11, 2019 - Jan 21, 2019 (10 days)",
        )

    def test_control_property_returns_experiment_control(self):
        experiment = ExperimentFactory.create_with_variants()
        control = ExperimentVariant.objects.get(
            experiment=experiment, is_control=True
        )
        self.assertEqual(experiment.control, control)

    def test_grouped_changes_groups_by_date_then_user(self):
        experiment = ExperimentFactory.create()

        date1 = timezone.now() - datetime.timedelta(days=2)
        date2 = timezone.now() - datetime.timedelta(days=1)
        date3 = timezone.now()

        user1 = UserFactory.create()
        user2 = UserFactory.create()
        user3 = UserFactory.create()

        change1 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date1
        )
        change2 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date1
        )
        change3 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date1
        )
        change4 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user2, changed_on=date1
        )

        change5 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user2, changed_on=date2
        )
        change6 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user3, changed_on=date2
        )
        change7 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user3, changed_on=date2
        )

        change8 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date3
        )
        change9 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date3
        )
        change10 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user2, changed_on=date3
        )
        change11 = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user3, changed_on=date3
        )

        self.assertEqual(
            set(experiment.grouped_changes.keys()),
            set([date1.date(), date2.date(), date3.date()]),
        )
        self.assertEqual(
            set(experiment.grouped_changes[date1.date()].keys()),
            set([user1, user2]),
        )
        self.assertEqual(
            set(experiment.grouped_changes[date2.date()].keys()),
            set([user2, user3]),
        )
        self.assertEqual(
            set(experiment.grouped_changes[date3.date()].keys()),
            set([user1, user2, user3]),
        )

        self.assertEqual(
            experiment.grouped_changes[date1.date()][user1],
            set([change1, change2, change3]),
        )
        self.assertEqual(
            experiment.grouped_changes[date1.date()][user2], set([change4])
        )

        self.assertEqual(
            experiment.grouped_changes[date2.date()][user2], set([change5])
        )
        self.assertEqual(
            experiment.grouped_changes[date2.date()][user3],
            set([change6, change7]),
        )

        self.assertEqual(
            experiment.grouped_changes[date3.date()][user1],
            set([change8, change9]),
        )
        self.assertEqual(
            experiment.grouped_changes[date3.date()][user2], set([change10])
        )
        self.assertEqual(
            experiment.grouped_changes[date3.date()][user3], set([change11])
        )

    def test_ordered_changes_orders_by_date(self):
        experiment = ExperimentFactory.create()

        date1 = timezone.now() - datetime.timedelta(days=2)
        date2 = timezone.now() - datetime.timedelta(days=1)
        date3 = timezone.now()

        user1 = UserFactory.create()
        user2 = UserFactory.create()
        user3 = UserFactory.create()

        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user1,
            changed_on=date1,
            message="a",
        )
        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user1,
            changed_on=date1,
            message="b",
        )
        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user1,
            changed_on=date1,
            message="b",
        )
        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user2,
            changed_on=date1,
            message="c",
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user2,
            changed_on=date2,
            message="d",
        )
        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user3,
            changed_on=date2,
            message="e",
        )
        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user3,
            changed_on=date2,
            message="f",
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user1,
            changed_on=date3,
            message="g",
        )
        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user1,
            changed_on=date3,
            message="h",
        )
        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user2,
            changed_on=date3,
            message="i",
        )
        ExperimentChangeLogFactory.create(
            experiment=experiment,
            changed_by=user3,
            changed_on=date3,
            message="j",
        )

        expected_changes = {
            date1.date(): {user1: set(["a", "b"]), user2: set(["c"])},
            date2.date(): {user2: set(["d"]), user3: set(["e", "f"])},
            date3.date(): {
                user1: set(["g", "h"]),
                user2: set(["i"]),
                user3: set(["j"]),
            },
        }

        ordered_dates = [date for date, changes in experiment.ordered_changes]
        self.assertEqual(
            ordered_dates, [date3.date(), date2.date(), date1.date()]
        )

        day3_users = [
            user for user, user_changes in experiment.ordered_changes[0][1]
        ]
        self.assertEqual(set(day3_users), set([user1, user2, user3]))

        day2_users = [
            user for user, user_changes in experiment.ordered_changes[1][1]
        ]
        self.assertEqual(set(day2_users), set([user2, user3]))

        day1_users = [
            user for user, user_changes in experiment.ordered_changes[2][1]
        ]
        self.assertEqual(set(day1_users), set([user1, user2]))

        for date, date_changes in experiment.ordered_changes:
            for user, user_changes in date_changes:
                self.assertEqual(user_changes, expected_changes[date][user])

    def test_experiment_is_editable_as_draft(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        self.assertTrue(experiment.is_editable)

    def test_experiment_is_editable_as_review(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW
        )
        self.assertTrue(experiment.is_editable)

    def test_experient_is_not_editable_after_review(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP
        )
        self.assertFalse(experiment.is_editable)

    def test_experiment_is_not_begun(self):
        statuses = (
            Experiment.STATUS_DRAFT,
            Experiment.STATUS_REVIEW,
            Experiment.STATUS_REJECTED,
        )

        for status in statuses:
            experiment = ExperimentFactory.create_with_status(status)
            self.assertFalse(experiment.is_begun)

    def test_experiment_is_begun(self):
        for status in Experiment.STATUS_LIVE, Experiment.STATUS_COMPLETE:
            experiment = ExperimentFactory.create_with_status(status)
            self.assertTrue(experiment.is_begun)

    def test_overview_is_not_complete_when_not_saved(self):
        experiment = ExperimentFactory.build()
        self.assertFalse(experiment.completed_overview)

    def test_overview_is_complete_when_saved(self):
        experiment = ExperimentFactory.create()
        self.assertTrue(experiment.completed_overview)

    def test_population_is_not_complete_when_defaults_set(self):
        experiment = ExperimentFactory.create(
            population_percent=0.0, firefox_min_version="", firefox_channel=""
        )
        self.assertFalse(experiment.completed_population)

    def test_population_is_complete_when_values_set(self):
        experiment = ExperimentFactory.create()
        self.assertTrue(experiment.completed_population)

    def test_variants_is_not_complete_when_no_variants_saved(self):
        experiment = ExperimentFactory.create()
        self.assertFalse(experiment.completed_variants)

    def test_variants_is_complete_when_variants_saved(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertTrue(experiment.completed_variants)

    def test_objectives_is_not_complete_with_still_default(self):
        experiment = ExperimentFactory.create(
            objectives=Experiment.OBJECTIVES_DEFAULT,
            analysis=Experiment.ANALYSIS_DEFAULT,
        )
        self.assertFalse(experiment.completed_objectives)

    def test_objectives_is_complete_with_non_defaults(self):
        experiment = ExperimentFactory.create(
            objectives="Some objectives!", analysis="Some analysis!"
        )
        self.assertTrue(experiment.completed_objectives)

    def test_risk_questions_returns_a_tuple(self):
        experiment = ExperimentFactory.create(
            risk_partner_related=False,
            risk_brand=True,
            risk_fast_shipped=False,
            risk_confidential=True,
            risk_release_population=False,
            risk_technical=True,
        )
        self.assertEqual(
            experiment._risk_questions, (False, True, False, True, False, True)
        )

    def test_risk_not_completed_when_risk_questions_not_answered(self):
        experiment = ExperimentFactory.create(
            risk_partner_related=None,
            risk_brand=None,
            risk_fast_shipped=None,
            risk_confidential=None,
            risk_release_population=None,
            testing="A test plan!",
        )
        self.assertFalse(experiment.completed_risks)

    def test_risk_completed_when_risk_questions_and_testing_completed(self):
        experiment = ExperimentFactory.create(
            risk_partner_related=False,
            risk_brand=True,
            risk_fast_shipped=False,
            risk_confidential=True,
            risk_release_population=False,
            testing="A test plan!",
        )
        self.assertTrue(experiment.completed_risks)

    def test_is_not_high_risk_if_no_risk_questions_are_true(self):
        experiment = ExperimentFactory.create(
            risk_partner_related=False,
            risk_brand=False,
            risk_fast_shipped=False,
            risk_confidential=False,
            risk_release_population=False,
        )
        self.assertFalse(experiment.is_high_risk)

    def test_is_high_risk_if_any_risk_questions_are_true(self):
        risk_fields = (
            "risk_partner_related",
            "risk_brand",
            "risk_fast_shipped",
            "risk_confidential",
            "risk_release_population",
        )

        for true_risk_field in risk_fields:
            instance_risk_fields = {field: False for field in risk_fields}
            instance_risk_fields[true_risk_field] = True

            experiment = ExperimentFactory.create(**instance_risk_fields)
            self.assertTrue(experiment.is_high_risk)

    def test_completed_required_reviews_false_when_reviews_not_complete(self):
        experiment = ExperimentFactory.create()
        self.assertFalse(experiment.completed_required_reviews)

    def test_completed_required_reviews_true_when_reviews_complete(self):
        experiment = ExperimentFactory.create(
            review_science=True,
            review_engineering=True,
            review_qa_requested=True,
            review_intent_to_ship=True,
            review_bugzilla=True,
            review_qa=True,
            review_relman=True,
        )
        self.assertTrue(experiment.completed_required_reviews)

    def test_completed_all_sections_false_when_incomplete(self):
        experiment = ExperimentFactory.create()
        self.assertFalse(experiment.completed_all_sections)

    def test_completed_all_sections_true_when_complete(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW
        )
        self.assertTrue(experiment.completed_all_sections)

    def test_is_ready_to_launch_true_when_reviews_and_sections_complete(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            review_science=True,
            review_engineering=True,
            review_qa_requested=True,
            review_intent_to_ship=True,
            review_bugzilla=True,
            review_qa=True,
            review_relman=True,
        )
        self.assertTrue(experiment.is_ready_to_launch)

    def test_experiment_population_returns_correct_string(self):
        experiment = ExperimentFactory(
            population_percent="0.5",
            firefox_min_version="57.0",
            firefox_channel="Nightly",
        )
        self.assertEqual(experiment.population, "0.5% of Nightly Firefox 57.0")


class TestExperimentChangeLog(TestCase):

    def test_latest_returns_most_recent_changelog(self):
        now = timezone.now()
        experiment = ExperimentFactory.create_with_variants()

        changelog1 = ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=None,
            new_status=Experiment.STATUS_DRAFT,
            changed_on=(now - datetime.timedelta(days=2)),
        )

        self.assertEqual(experiment.changes.latest(), changelog1)

        changelog2 = ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=Experiment.STATUS_DRAFT,
            new_status=Experiment.STATUS_REVIEW,
            changed_on=(now - datetime.timedelta(days=1)),
        )

        self.assertEqual(experiment.changes.latest(), changelog2)

    def test_pretty_status_created_draft(self):
        experiment = ExperimentFactory.create_with_variants()

        for old_status in ExperimentChangeLog.PRETTY_STATUS_LABELS.keys():
            for new_status in ExperimentChangeLog.PRETTY_STATUS_LABELS[
                old_status
            ].keys():
                expected_label = ExperimentChangeLog.PRETTY_STATUS_LABELS[
                    old_status
                ][new_status]

                changelog = ExperimentChangeLogFactory.create(
                    experiment=experiment,
                    old_status=old_status,
                    new_status=new_status,
                )
                self.assertEqual(changelog.pretty_status, expected_label)


class TestExperimentComments(TestCase):

    def test_manager_returns_sections(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT
        )
        risk_comment = ExperimentCommentFactory.create(
            experiment=experiment, section=Experiment.SECTION_RISKS
        )
        testing_comment = ExperimentCommentFactory.create(
            experiment=experiment, section=Experiment.SECTION_TESTING
        )
        self.assertIn(
            risk_comment,
            experiment.comments.sections[experiment.SECTION_RISKS],
        )
        self.assertIn(
            testing_comment,
            experiment.comments.sections[experiment.SECTION_TESTING],
        )
        self.assertNotIn(
            risk_comment,
            experiment.comments.sections[experiment.SECTION_TESTING],
        )
        self.assertNotIn(
            testing_comment,
            experiment.comments.sections[experiment.SECTION_RISKS],
        )
