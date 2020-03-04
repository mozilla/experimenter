import datetime
import json

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from django.db.utils import IntegrityError

from experimenter.openidc.tests.factories import UserFactory
from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    VariantPreferences,
    ExperimentChangeLog,
)
from experimenter.experiments.serializers.recipe import ExperimentRecipeSerializer
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
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
        self.assertEqual(experiment.get_absolute_url(), "/experiments/experiment-slug/")

    def test_experiment_url(self):
        experiment = ExperimentFactory.create(slug="experiment-slug")
        self.assertEqual(
            experiment.experiment_url,
            f"https://{settings.HOSTNAME}/experiments/experiment-slug/",
        )

    def test_bugzilla_url_returns_none_if_bugzilla_id_not_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, bugzilla_id=None
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

    def test_monitoring_dashboard_url_is_none_when_experiment_not_begun(self):
        experiment = ExperimentFactory.create(
            slug="experiment",
            status=Experiment.STATUS_DRAFT,
            normandy_slug="normandy-slug",
        )
        self.assertIsNone(experiment.monitoring_dashboard_url)

    def test_monitoring_dashboard_url_returns_url_when_experiment_is_begun(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            slug="experiment",
            status=Experiment.STATUS_LIVE,
            normandy_slug="normandy-slug",
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=Experiment.STATUS_ACCEPTED,
            new_status=Experiment.STATUS_LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )

        changed_on_in_milliseconds = 1556582400000

        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.normandy_slug,
                from_date=changed_on_in_milliseconds,
                to_date="",
            ),
        )

    def test_monitoring_dashboard_url_returns_url_when_experiment_is_complete(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            slug="experiment",
            status=Experiment.STATUS_COMPLETE,
            normandy_slug="normandy-slug",
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=Experiment.STATUS_ACCEPTED,
            new_status=Experiment.STATUS_LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=Experiment.STATUS_LIVE,
            new_status=Experiment.STATUS_COMPLETE,
            changed_on=datetime.date(2019, 5, 10),
        )

        started_on_in_milliseconds = 1556582400000
        completed_on_in_milliseconds = 1557619200000

        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.normandy_slug,
                from_date=started_on_in_milliseconds,
                to_date=completed_on_in_milliseconds,
            ),
        )

    def test_monitoring_dashboard_url_returns_url_when_experiment_is_addon(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ADDON,
            slug="experiment",
            status=Experiment.STATUS_LIVE,
            normandy_slug="normandy-slug",
        )

        ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=Experiment.STATUS_ACCEPTED,
            new_status=Experiment.STATUS_LIVE,
            changed_on=datetime.date(2019, 5, 1),
        )

        changed_on_in_milliseconds = 1556582400000

        self.assertEqual(
            experiment.monitoring_dashboard_url,
            settings.MONITORING_URL.format(
                slug=experiment.normandy_slug,
                from_date=changed_on_in_milliseconds,
                to_date="",
            ),
        )

    def test_has_external_urls_is_false_when_no_external_urls(self):
        experiment = ExperimentFactory.create(
            bugzilla_id="", data_science_bugzilla_url="", feature_bugzilla_url=""
        )
        self.assertFalse(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_data_science_bugzilla_url_is_set(self):
        experiment = ExperimentFactory.create(
            data_science_bugzilla_url="www.bugzilla.com/show_bug.cgi?id=123/"
        )
        self.assertTrue(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_feature_bugzilla_url_is_set(self):
        experiment = ExperimentFactory.create(
            feature_bugzilla_url="www.bugzilla.com/show_bug.cgi?id=123/"
        )
        self.assertTrue(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_bugzilla_url_is_set(self):
        experiment = ExperimentFactory.create(bugzilla_id="1234")
        self.assertTrue(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_monitoring_dashboard_url_is_set(self):
        experiment = ExperimentFactory.create(
            status=Experiment.STATUS_LIVE, normandy_slug="normandy-slug"
        )
        self.assertTrue(experiment.has_external_urls)

    def test_has_external_urls_is_true_when_bugzilla_and_monitoring_set(self):
        experiment = ExperimentFactory.create(
            status=Experiment.STATUS_LIVE,
            bugzilla_id="1234",
            normandy_slug="normandy-slug",
        )
        self.assertTrue(experiment.has_external_urls)

    def test_should_use_normandy_false_for_generic(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_GENERIC)
        self.assertFalse(experiment.should_use_normandy)

    def test_should_use_normandy_true_for_pref(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_PREF)
        self.assertTrue(experiment.should_use_normandy)

    def test_should_use_normandy_true_for_addon(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ADDON)
        self.assertTrue(experiment.should_use_normandy)

    def test_generate_normandy_slug_raises_valueerror_without_version(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            slug="experiment-slug",
            firefox_min_version="",
            firefox_channel="Nightly",
            bugzilla_id="12345",
        )

        with self.assertRaises(ValueError):
            experiment.generate_normandy_slug()

    def test_generate_normandy_slug_raises_valueerror_without_channel(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            slug="experiment-slug",
            firefox_min_version="57.0",
            firefox_channel="",
            bugzilla_id="12345",
        )

        with self.assertRaises(ValueError):
            experiment.generate_normandy_slug()

    def test_generate_normandy_slug_raises_valueerror_without_bugzilla(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            slug="experiment-slug",
            firefox_min_version="57.0",
            firefox_channel="Nightly",
            bugzilla_id="",
        )

        with self.assertRaises(ValueError):
            experiment.generate_normandy_slug()

    def test_generate_normandy_slug_returns_slug_with_min_max_version(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            name="Experiment Name",
            slug="experiment-slug",
            firefox_min_version="57.0",
            firefox_max_version="59.0",
            firefox_channel="Nightly",
            bugzilla_id="12345",
        )

        self.assertEqual(
            experiment.generate_normandy_slug(),
            "pref-experiment-name-nightly-57-59-bug-12345",
        )

    def test_generate_normandy_slug_returns_slug_with_min_version(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            name="Experiment Name",
            slug="experiment-slug",
            firefox_min_version="57.0",
            firefox_max_version="",
            firefox_channel="Nightly",
            bugzilla_id="12345",
        )

        self.assertEqual(
            experiment.generate_normandy_slug(),
            "pref-experiment-name-nightly-57-bug-12345",
        )

    def test_generate_normandy_slug_raises_valueerror_without_addon_info(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ADDON,
            addon_experiment_id=None,
            firefox_min_version="60.0",
        )

        with self.assertRaises(ValueError):
            experiment.generate_normandy_slug()

    def test_generate_normandy_slug_uses_addon_info_for_addon_experiment(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ADDON,
            addon_experiment_id="addon_experiment_id",
            firefox_min_version="60.0",
        )

        self.assertEqual(experiment.generate_normandy_slug(), "addon_experiment_id")

    def test_generate_normandy_slug_uses_addon_info_for_branched_addon_experiment(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ADDON,
            name="some random name",
            firefox_min_version="70.0",
            firefox_max_version="71.0",
            firefox_channel=Experiment.CHANNEL_BETA,
        )
        self.assertEqual(
            "addon-some-random-name-beta-70-71-bug-12345",
            experiment.generate_normandy_slug(),
        )

    def test_generate_normandy_slug_is_shorter_than_max_normandy_len(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            name="a" * (settings.NORMANDY_SLUG_MAX_LEN + 1),
            firefox_min_version="57.0",
            firefox_max_version="59.0",
            firefox_channel="Nightly",
            bugzilla_id="12345",
        )

        self.assertGreater(len(experiment.name), settings.NORMANDY_SLUG_MAX_LEN)

        normandy_slug = experiment.generate_normandy_slug()

        self.assertEqual(len(normandy_slug), settings.NORMANDY_SLUG_MAX_LEN)

    def test_is_rollout_false_for_not_type_rollout(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_PREF)
        self.assertFalse(experiment.is_rollout)

    def test_is_rollout_true_for_type_rollout(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)
        self.assertTrue(experiment.is_rollout)

    def test_is_pref_rollout(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT, rollout_type=Experiment.TYPE_PREF
        )
        self.assertTrue(experiment.is_pref_rollout)

    def test_is_addon_rollout(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT, rollout_type=Experiment.TYPE_ADDON
        )
        self.assertTrue(experiment.is_addon_rollout)

    def test_normandy_recipe_json_serializes_pref_study(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_SHIP)
        recipe_json = json.loads(experiment.normandy_recipe_json)
        self.assertEqual(recipe_json, ExperimentRecipeSerializer(experiment).data)

    def test_has_normandy_info_not_true_if_missing_normandy_info(self):
        experiment = ExperimentFactory.create(normandy_id=None, normandy_slug=None)
        self.assertFalse(experiment.has_normandy_info)

    def test_has_normandy_info_true_with_normandy_slug(self):
        experiment = ExperimentFactory.create(normandy_id=None, normandy_slug="abc")
        self.assertTrue(experiment.has_normandy_info)

    def test_has_normandy_info_true_with_normandy_id(self):
        experiment = ExperimentFactory.create(normandy_id="123", normandy_slug=None)
        self.assertTrue(experiment.has_normandy_info)

    def test_format_dc_normandy_urls_returns_empty_list_without_normandy_id(self):
        experiment = ExperimentFactory.create(normandy_id=None)
        self.assertEqual(len(experiment.format_dc_normandy_urls), 0)

    def test_format_dc_normandy_urls_with_only_main(self):
        experiment = ExperimentFactory.create(normandy_id="445")
        with override_settings(
            DELIVERY_CONSOLE_RECIPE_URL=(
                "http://delivery-console.example.com/recipe/{id}/"
            )
        ):
            self.assertEqual(
                experiment.format_dc_normandy_urls[0]["DC_url"],
                "http://delivery-console.example.com/recipe/445/",
            )

        with override_settings(
            NORMANDY_API_RECIPE_URL="http://normandy.example.com/recipe/{id}/"
        ):
            self.assertEqual(
                experiment.format_dc_normandy_urls[0]["normandy_url"],
                "http://normandy.example.com/recipe/445/",
            )

    def test_format_dc_normandy_urls_with_main_and_other_ids(self):
        experiment = ExperimentFactory.create(
            normandy_id="32", other_normandy_ids=[43, 56]
        )
        with override_settings(
            DELIVERY_CONSOLE_RECIPE_URL=(
                "http://delivery-console.example.com/recipe/{id}/"
            ),
            NORMANDY_API_RECIPE_URL="http://normandy.example.com/recipe/{id}/",
        ):
            self.assertEqual(
                experiment.format_dc_normandy_urls[0]["DC_url"],
                "http://delivery-console.example.com/recipe/32/",
            )
            self.assertEqual(
                experiment.format_dc_normandy_urls[0]["normandy_url"],
                "http://normandy.example.com/recipe/32/",
            )
            self.assertEqual(
                experiment.format_dc_normandy_urls[1]["DC_url"],
                "http://delivery-console.example.com/recipe/43/",
            )
            self.assertEqual(
                experiment.format_dc_normandy_urls[1]["normandy_url"],
                "http://normandy.example.com/recipe/43/",
            )
            self.assertEqual(
                experiment.format_dc_normandy_urls[2]["DC_url"],
                "http://delivery-console.example.com/recipe/56/",
            )
            self.assertEqual(
                experiment.format_dc_normandy_urls[2]["normandy_url"],
                "http://normandy.example.com/recipe/56/",
            )

    def test_start_date_returns_proposed_start_date_if_change_is_missing(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertEqual(experiment.start_date, experiment.proposed_start_date)

    def test_start_date_returns_datetime_if_change_exists(self):
        change = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_ACCEPTED, new_status=Experiment.STATUS_LIVE
        )
        self.assertEqual(change.experiment.start_date, change.changed_on.date())

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
        experiment = ExperimentFactory.create_with_variants(proposed_start_date=None)
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
        self.assertEqual(experiment._compute_end_date(10), datetime.date(2019, 1, 11))

    def test_compute_end_date_accepts_invalid_duration(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1)
        )
        self.assertEqual(experiment._compute_end_date(experiment.MAX_DURATION + 1), None)

    def test_end_date_uses_duration_if_change_is_missing(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1), proposed_duration=20
        )

        self.assertEqual(experiment.end_date, datetime.date(2019, 1, 21))

    def test_end_date_returns_datetime_if_change_exists(self):
        change = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_LIVE, new_status=Experiment.STATUS_COMPLETE
        )
        self.assertEqual(change.experiment.end_date, change.changed_on.date())

    def test_enrollment_end_date_uses_enrollment_duration(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1),
            proposed_duration=20,
            proposed_enrollment=10,
        )
        self.assertEqual(experiment.end_date, datetime.date(2019, 1, 21))

    def test_enrollment_ending_soon(self):
        experiment_1 = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date.today(),
            proposed_duration=20,
            proposed_enrollment=5,
        )
        self.assertTrue(experiment_1.enrollment_ending_soon)

        experiment_2 = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date.today(),
            proposed_duration=20,
            proposed_enrollment=8,
        )
        self.assertFalse(experiment_2.enrollment_ending_soon)

    def test_experiment_ending_soon(self):
        experiment_1 = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date.today(),
            proposed_duration=5,
            proposed_enrollment=0,
        )
        self.assertTrue(experiment_1.ending_soon)

        experiment_2 = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date.today(),
            proposed_duration=20,
            proposed_enrollment=0,
        )
        self.assertFalse(experiment_2.ending_soon)

    def test_format_date_string_accepts_none_for_start(self):
        experiment = ExperimentFactory.create_with_variants()
        output = experiment._format_date_string(None, datetime.date(2019, 1, 1))
        self.assertEqual(output, "Unknown - Jan 01, 2019 (Unknown days)")

    def test_format_date_string_accepts_none_for_end(self):
        experiment = ExperimentFactory.create_with_variants()
        output = experiment._format_date_string(datetime.date(2019, 1, 1), None)
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
        self.assertEqual(experiment.dates, "Jan 01, 2019 - Jan 21, 2019 (20 days)")

    def test_enrollment_dates_returns_date_string(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1),
            proposed_duration=20,
            proposed_enrollment=10,
        )
        self.assertEqual(
            experiment.enrollment_dates, "Jan 01, 2019 - Jan 11, 2019 (10 days)"
        )

    def test_observation_dates_returns_date_string(self):
        experiment = ExperimentFactory.create_with_variants(
            proposed_start_date=datetime.date(2019, 1, 1),
            proposed_duration=20,
            proposed_enrollment=10,
        )
        self.assertEqual(
            experiment.observation_dates, "Jan 11, 2019 - Jan 21, 2019 (10 days)"
        )

    def test_rollout_dates_low_risk_playbook(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            rollout_playbook=Experiment.ROLLOUT_PLAYBOOK_LOW_RISK,
            proposed_start_date=datetime.date(2020, 1, 1),
        )
        self.assertEqual(
            experiment.rollout_dates,
            {
                "first_increase": {"date": "Jan 01, 2020", "percent": "25"},
                "second_increase": {"date": "Jan 08, 2020", "percent": "75"},
                "final_increase": {"date": "Jan 22, 2020", "percent": "100"},
            },
        )

    def test_rollout_dates_high_risk_playbook(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            rollout_playbook=Experiment.ROLLOUT_PLAYBOOK_HIGH_RISK,
            proposed_start_date=datetime.date(2020, 1, 1),
        )
        self.assertEqual(
            experiment.rollout_dates,
            {
                "first_increase": {"date": "Jan 01, 2020", "percent": "25"},
                "second_increase": {"date": "Jan 08, 2020", "percent": "50"},
                "final_increase": {"date": "Jan 22, 2020", "percent": "100"},
            },
        )

    def test_rollout_dates_marketing_playbook(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            rollout_playbook=Experiment.ROLLOUT_PLAYBOOK_MARKETING,
            proposed_start_date=datetime.date(2020, 1, 1),
        )
        self.assertEqual(
            experiment.rollout_dates,
            {"final_increase": {"date": "Jan 01, 2020", "percent": "100"}},
        )

    def test_rollout_dates_custom_playbook(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            rollout_playbook=Experiment.ROLLOUT_PLAYBOOK_CUSTOM,
            proposed_start_date=datetime.date(2020, 1, 1),
        )
        self.assertEqual(experiment.rollout_dates, {})

    def test_enrollment_is_complete(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, is_paused=True
        )
        self.assertTrue(experiment.is_enrollment_complete)

    def test_enrollment_is_not_complete(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, is_paused=False
        )
        self.assertFalse(experiment.is_enrollment_complete)

    def test_control_property_returns_experiment_control(self):
        experiment = ExperimentFactory.create_with_variants()
        control = ExperimentVariant.objects.get(experiment=experiment, is_control=True)
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
            set(experiment.grouped_changes[date1.date()].keys()), set([user1, user2])
        )
        self.assertEqual(
            set(experiment.grouped_changes[date2.date()].keys()), set([user2, user3])
        )
        self.assertEqual(
            set(experiment.grouped_changes[date3.date()].keys()),
            set([user1, user2, user3]),
        )

        self.assertEqual(
            experiment.grouped_changes[date1.date()][user1],
            set([change1, change2, change3]),
        )
        self.assertEqual(experiment.grouped_changes[date1.date()][user2], set([change4]))

        self.assertEqual(experiment.grouped_changes[date2.date()][user2], set([change5]))
        self.assertEqual(
            experiment.grouped_changes[date2.date()][user3], set([change6, change7])
        )

        self.assertEqual(
            experiment.grouped_changes[date3.date()][user1], set([change8, change9])
        )
        self.assertEqual(experiment.grouped_changes[date3.date()][user2], set([change10]))
        self.assertEqual(experiment.grouped_changes[date3.date()][user3], set([change11]))

    def test_ordered_changes_orders_by_date(self):
        experiment = ExperimentFactory.create()

        date1 = timezone.now() - datetime.timedelta(days=2)
        date2 = timezone.now() - datetime.timedelta(days=1)
        date3 = timezone.now()

        user1 = UserFactory.create()
        user2 = UserFactory.create()
        user3 = UserFactory.create()

        a = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date1, message="a"
        )
        b = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date1, message="b"
        )

        c = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user2, changed_on=date1, message="c"
        )

        d = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user2, changed_on=date2, message="d"
        )
        e = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user3, changed_on=date2, message="e"
        )
        f = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user3, changed_on=date2, message="f"
        )

        g = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date3, message="g"
        )
        h = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user1, changed_on=date3, message="h"
        )
        i = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user2, changed_on=date3, message="i"
        )
        j = ExperimentChangeLogFactory.create(
            experiment=experiment, changed_by=user3, changed_on=date3, message="j"
        )

        expected_changes = {
            date1.date(): {user1: set([a, b]), user2: set([c])},
            date2.date(): {user2: set([d]), user3: set([e, f])},
            date3.date(): {user1: set([g, h]), user2: set([i]), user3: set([j])},
        }

        ordered_dates = [date for date, changes in experiment.ordered_changes]
        self.assertEqual(ordered_dates, [date3.date(), date2.date(), date1.date()])

        day3_users = [user for user, user_changes in experiment.ordered_changes[0][1]]
        self.assertEqual(set(day3_users), set([user1, user2, user3]))

        day2_users = [user for user, user_changes in experiment.ordered_changes[1][1]]
        self.assertEqual(set(day2_users), set([user2, user3]))

        day1_users = [user for user, user_changes in experiment.ordered_changes[2][1]]
        self.assertEqual(set(day1_users), set([user1, user2]))

        for date, date_changes in experiment.ordered_changes:
            for user, user_changes in date_changes:
                self.assertEqual(user_changes, expected_changes[date][user])

    def test_experiment_is_editable_as_draft(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        self.assertTrue(experiment.is_editable)

    def test_experiment_is_editable_as_review(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)
        self.assertTrue(experiment.is_editable)

    def test_experient_is_not_editable_after_review(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_SHIP)
        self.assertFalse(experiment.is_editable)

    def test_experiment_is_not_begun(self):
        statuses = (Experiment.STATUS_DRAFT, Experiment.STATUS_REVIEW)

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

    def test_timeline_is_not_complete_when_missing_dates(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF, proposed_start_date=None, proposed_duration=None
        )
        self.assertFalse(experiment.completed_timeline)

    def test_timeline_is_complete_when_dates_set(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_PREF,
            proposed_start_date=datetime.date.today(),
            proposed_duration=10,
        )
        self.assertTrue(experiment.completed_timeline)

    def test_timeline_is_not_complete_when_missing_playbook_for_rollout(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            proposed_start_date=datetime.date.today(),
            proposed_duration=10,
        )
        self.assertFalse(experiment.completed_timeline)

    def test_timeline_is_complete_with_playbook_for_rollout(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            proposed_start_date=datetime.date.today(),
            proposed_duration=10,
            rollout_playbook=Experiment.ROLLOUT_PLAYBOOK_CUSTOM,
        )
        self.assertTrue(experiment.completed_timeline)

    def test_population_is_not_complete_when_defaults_set(self):
        experiment = ExperimentFactory.create(
            population_percent=0.0, firefox_min_version="", firefox_channel=""
        )
        self.assertFalse(experiment.completed_population)

    def test_population_is_complete_when_values_set(self):
        experiment = ExperimentFactory.create()
        self.assertTrue(experiment.completed_population)

    def test_population_is_complete_for_rollout_without_population_percent(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT, population_percent=0.0
        )
        self.assertTrue(experiment.completed_population)

    def test_design_is_not_complete_when_defaults_set(self):
        experiment = ExperimentFactory.create(design=Experiment.DESIGN_DEFAULT)
        self.assertFalse(experiment.completed_design)

    def test_design_is_complete_when_design_set(self):
        experiment = ExperimentFactory.create(design="Design")
        self.assertTrue(experiment.completed_design)

    def test_addons_is_not_complete_when_release_url_not_set(self):
        experiment = ExperimentFactory.create(
            addon_experiment_id=None, addon_release_url=None
        )
        self.assertFalse(experiment.completed_addon)

    def test_addons_is_complete_when_release_url_set(self):
        experiment = ExperimentFactory.create(
            addon_experiment_id="addon-experiment-id",
            addon_release_url="https://www.example.com/release.xpi",
        )
        self.assertTrue(experiment.completed_addon)

    def test_completed_addon_is_not_complete_when_release_url_not_set_for_branched(self):
        experiment = ExperimentFactory.create_with_variants(
            type=Experiment.TYPE_ADDON, is_branched_addon=True
        )
        variant = experiment.variants.first()
        variant.addon_release_url = None
        variant.save()

        self.assertFalse(experiment.completed_addon)

    def test_completed_addon_complete_when_release_url_for_each_branch_set_for_branched(
        self
    ):
        experiment = ExperimentFactory.create_with_variants(
            type=Experiment.TYPE_ADDON, is_branched_addon=True
        )
        for variant in experiment.variants.all():
            self.assertTrue(variant.addon_release_url)

        self.assertTrue(experiment.completed_addon)

    def test_variants_is_not_complete_when_no_variants_saved(self):
        experiment = ExperimentFactory.create()
        self.assertFalse(experiment.completed_variants)

    def test_variants_is_complete_when_variants_saved(self):
        experiment = ExperimentFactory.create_with_variants()
        self.assertTrue(experiment.completed_variants)

    def test_objectives_is_not_complete_with_still_default(self):
        experiment = ExperimentFactory.create(
            objectives=Experiment.OBJECTIVES_DEFAULT, analysis=Experiment.ANALYSIS_DEFAULT
        )
        self.assertFalse(experiment.completed_objectives)

    def test_objectives_is_complete_with_non_defaults(self):
        experiment = ExperimentFactory.create(
            objectives="Some objectives!", analysis="Some analysis!"
        )
        self.assertTrue(experiment.completed_objectives)

    def test_addon_rollout_completed(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            rollout_type=Experiment.TYPE_ADDON,
            addon_release_url="https://example.com/addon.xpi",
        )
        self.assertTrue(experiment.completed_addon_rollout)

    def test_pref_rollout_completed(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            rollout_type=Experiment.TYPE_PREF,
            pref_type=Experiment.PREF_TYPE_STR,
            pref_name="abc",
            pref_value="abc",
        )
        self.assertTrue(experiment.completed_pref_rollout)

    def test_rollout_completed_for_pref(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            rollout_type=Experiment.TYPE_PREF,
            pref_type=Experiment.PREF_TYPE_STR,
            pref_name="abc",
            pref_value="abc",
        )
        self.assertTrue(experiment.completed_rollout)

    def test_is_pref_value_json_string_returns_true(self):
        experiment = ExperimentFactory.create(pref_type=Experiment.PREF_TYPE_JSON_STR)
        self.assertTrue(experiment.is_pref_value_json_string)

    def test_is_pref_value_jsons_string_returns_false_for_non_json_type(self):
        experiment = ExperimentFactory.create(pref_type=Experiment.PREF_TYPE_INT)
        self.assertFalse(experiment.is_pref_value_json_string)

    def test_rollout_completed_for_addon(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            rollout_type=Experiment.TYPE_ADDON,
            addon_release_url="https://example.com/addon.xpi",
        )
        self.assertTrue(experiment.completed_rollout)

    def test_risk_questions_returns_a_tuple(self):
        experiment = ExperimentFactory.create(
            risk_partner_related=False,
            risk_brand=True,
            risk_fast_shipped=False,
            risk_confidential=True,
            risk_release_population=False,
            risk_revenue=True,
            risk_data_category=False,
            risk_external_team_impact=True,
            risk_telemetry_data=False,
            risk_ux=True,
            risk_security=False,
            risk_revision=True,
            risk_technical=False,
            risk_higher_risk=True,
        )
        self.assertEqual(
            experiment._risk_questions,
            [
                False,
                True,
                False,
                True,
                False,
                True,
                False,
                True,
                False,
                True,
                False,
                True,
                False,
                True,
            ],
        )

    def test_risk_questions_returns_a_tuple_rollout(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            risk_partner_related=False,
            risk_brand=True,
            risk_fast_shipped=False,
            risk_confidential=True,
            risk_release_population=None,
            risk_revenue=True,
            risk_data_category=False,
            risk_external_team_impact=True,
            risk_telemetry_data=False,
            risk_ux=True,
            risk_security=False,
            risk_revision=True,
            risk_technical=False,
            risk_higher_risk=True,
        )
        self.assertEqual(
            experiment._risk_questions,
            [
                False,
                True,
                False,
                True,
                True,
                False,
                True,
                False,
                True,
                False,
                True,
                False,
                True,
            ],
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

    def test_risk_not_completed_when_technical_description_required(self):
        experiment = ExperimentFactory.create(
            risk_technical=True, risk_technical_description=""
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

    def test_lightning_advising_required_for_rollout(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            review_advisory=False,
            review_science=True,
            review_engineering=True,
            review_qa_requested=True,
            review_intent_to_ship=True,
            review_bugzilla=True,
            review_qa=True,
            review_relman=True,
        )
        self.assertFalse(experiment.completed_required_reviews)

    def test_required_reviews_for_rollout(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            review_advisory=True,
            review_science=True,
            review_qa_requested=True,
            review_intent_to_ship=True,
            review_qa=True,
            review_relman=True,
        )
        self.assertTrue(experiment.completed_required_reviews)

    def test_completed_all_sections_false_when_incomplete(self):
        experiment = ExperimentFactory.create()
        self.assertFalse(experiment.completed_all_sections)

    def test_completed_all_sections_true_when_complete(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)
        self.assertTrue(experiment.completed_all_sections)

    def test_completed_all_sections_true_for_pref_experiment_without_addon(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, type=Experiment.TYPE_PREF, addon_release_url=None
        )
        self.assertTrue(experiment.completed_all_sections)

    def test_completed_all_sections_false_for_addon_experiment_without_addon(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, type=Experiment.TYPE_ADDON, addon_release_url=None
        )
        self.assertFalse(experiment.completed_all_sections)

    def test_completed_all_sections_true_for_addon_experiment_with_addon(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            type=Experiment.TYPE_ADDON,
            addon_release_url="https://www.example.com/release.xpi",
        )
        self.assertTrue(experiment.completed_all_sections)

    def test_completed_all_sections_false_for_branchedadd_exp_without_url(self):
        experiment = ExperimentFactory.create_with_variants(
            is_branched_addon=True, type=Experiment.TYPE_ADDON
        )
        variant = experiment.variants.first()
        variant.addon_release_url = None
        variant.save()

        self.assertFalse(experiment.completed_all_sections)

    def test_completed_all_sections_true_for_branchedadd_exp_with_url(self):
        experiment = ExperimentFactory.create_with_variants(
            type=Experiment.TYPE_ADDON, is_branched_addon=True
        )

        for variant in experiment.variants.all():
            self.assertTrue(variant.addon_release_url)

        self.assertTrue(experiment.completed_all_sections)

    def test_completed_all_sections_false_for_generic_without_design(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            type=Experiment.TYPE_GENERIC,
            design=Experiment.DESIGN_DEFAULT,
        )
        self.assertFalse(experiment.completed_all_sections)

    def test_completed_all_sections_true_for_generic_with_design(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, type=Experiment.TYPE_GENERIC, design="Design"
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

    def test_is_ready_to_launch_true_with_conditional_review(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            review_science=True,
            review_engineering=True,
            review_qa_requested=True,
            review_intent_to_ship=True,
            review_bugzilla=True,
            review_qa=True,
            review_relman=True,
            review_vp=True,
            review_legal=True,
            risk_partner_related=True,
        )
        self.assertTrue(experiment.is_ready_to_launch)

    def test_is_ready_to_launch_is_false_without_conditional_review(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            review_science=True,
            review_engineering=True,
            review_qa_requested=True,
            review_intent_to_ship=True,
            review_bugzilla=True,
            review_qa=True,
            review_relman=True,
            risk_partner_related=True,
        )

        self.assertFalse(experiment.is_ready_to_launch)

    def test_review_order_is_correct_for_experiment(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_PREF)
        expected_reviews = [
            "review_science",
            "review_advisory",
            "review_engineering",
            "review_qa_requested",
            "review_intent_to_ship",
            "review_bugzilla",
            "review_qa",
            "review_relman",
        ]
        reviews = experiment.get_all_required_reviews()
        self.assertEqual(expected_reviews, reviews)

    def test_review_order_is_correct_for_rollout(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)
        expected_reviews = [
            "review_advisory",
            "review_qa_requested",
            "review_intent_to_ship",
            "review_qa",
            "review_relman",
        ]
        reviews = experiment.get_all_required_reviews()
        self.assertEqual(expected_reviews, reviews)

    def test_completed_results_returns_true_if_any_results(self):
        experiment = ExperimentFactory.create(
            results_initial="The results here were great."
        )
        self.assertTrue(experiment.completed_results)

    def test_completed_results_returns_false_if_none(self):
        experiment = ExperimentFactory.create(
            results_initial=None, results_url=None, results_lessons_learned=None
        )
        self.assertFalse(experiment.completed_results)

    def test_experiment_is_not_archivable(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_ACCEPTED
        )
        self.assertFalse(experiment.is_archivable)
        experiment2 = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE
        )
        self.assertFalse(experiment.is_archivable)
        self.assertFalse(experiment2.is_archivable)

    def test_experiment_is_archivable(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_DRAFT
        )
        self.assertTrue(experiment.is_archivable)

    def test_format_firefox_versions_returns_correct_string(self):
        experiment_1 = ExperimentFactory(
            firefox_min_version="57.0", firefox_max_version=""
        )
        experiment_2 = ExperimentFactory(
            firefox_min_version="57.0", firefox_max_version="59.0"
        )

        self.assertEqual(experiment_1.format_firefox_versions, "57.0")
        self.assertEqual(experiment_2.format_firefox_versions, "57.0 to 59.0")

    def test_versions_integer_list_with_only_min_returns_correct_list(self):
        experiment = ExperimentFactory(firefox_min_version="57.0", firefox_max_version="")

        self.assertEqual(experiment.versions_integer_list, [57])

    def test_versions_integer_list_with_min_max_returns_correct_list(self):
        experiment = ExperimentFactory(
            firefox_min_version="57.0", firefox_max_version="59.0"
        )

        self.assertEqual(experiment.versions_integer_list, [57, 58, 59])

    def test_firefox_max_version_integer_returns_correct_integer(self):
        experiment = ExperimentFactory(
            firefox_min_version="57.0", firefox_max_version="59.0"
        )

        self.assertEqual(experiment.firefox_max_version_integer, 59)

    def test_firefox_min_version_integer_returns_correct_integer(self):
        experiment = ExperimentFactory(
            firefox_min_version="57.0", firefox_max_version="59.0"
        )

        self.assertEqual(experiment.firefox_min_version_integer, 57)

    def test_use_branched_addon_serializer_returns_true_for_addon_and_greater_version(
        self
    ):
        experiment = ExperimentFactory(
            type=Experiment.TYPE_ADDON, firefox_min_version="70.0"
        )
        self.assertTrue(experiment.use_branched_addon_serializer)

    def test_use_branched_addon_serializer_returns_false_for_addon_and_lower_version(
        self
    ):
        experiment = ExperimentFactory(
            type=Experiment.TYPE_ADDON, firefox_min_version="66.0"
        )
        self.assertFalse(experiment.use_branched_addon_serializer)

    def test_use_branched_addon_serializer_returns_false_for_pref_type(self):
        experiment = ExperimentFactory()
        self.assertFalse(experiment.use_branched_addon_serializer)

    def test_is_multi_pref_returns_true_for_pref_and_greater_version(self):
        experiment = ExperimentFactory(
            type=Experiment.TYPE_PREF, firefox_min_version="70.0"
        )
        self.assertTrue(experiment.use_multi_pref_serializer)

    def test_is_multi_pref_returns_false_for_pref_and_lower_version(self):
        experiment = ExperimentFactory(
            type=Experiment.TYPE_PREF, firefox_min_version="66.0"
        )
        self.assertFalse(experiment.use_multi_pref_serializer)

    def test_is_multi_pref_returns_false_for_addon_type(self):
        experiment = ExperimentFactory(type=Experiment.TYPE_ADDON)
        self.assertFalse(experiment.use_multi_pref_serializer)

    def test_experiment_population_returns_correct_string(self):
        experiment = ExperimentFactory(
            type=Experiment.TYPE_PREF,
            population_percent="0.5",
            firefox_min_version="57.0",
            firefox_max_version="",
            firefox_channel="Nightly",
        )
        self.assertEqual(experiment.population, "0.5% of Nightly Firefox 57.0")

    def test_experiment_population_returns_correct_string_for_rollout(self):
        experiment = ExperimentFactory(
            type=Experiment.TYPE_ROLLOUT,
            firefox_min_version="57.0",
            firefox_max_version="",
            firefox_channel="Nightly",
        )
        self.assertEqual(experiment.population, "Nightly Firefox 57.0")

    def test_experiment_firefox_channel_sort_does_sorting(self):
        ExperimentFactory.create(firefox_channel=Experiment.CHANNEL_NIGHTLY)
        ExperimentFactory.create(firefox_channel=Experiment.CHANNEL_RELEASE)
        ExperimentFactory.create(firefox_channel=Experiment.CHANNEL_BETA)
        ExperimentFactory.create(firefox_channel="")
        sorted_experiments = (
            Experiment.objects.annotate(
                firefox_channel_sort=Experiment.firefox_channel_sort()
            )
            .order_by("firefox_channel_sort")
            .values("firefox_channel_sort")
        )
        self.assertEqual(
            [r["firefox_channel_sort"] for r in sorted_experiments],
            [
                Experiment.CHANNEL_UNSET_ORDER,
                Experiment.CHANNEL_NIGHTLY_ORDER,
                Experiment.CHANNEL_BETA_ORDER,
                Experiment.CHANNEL_RELEASE_ORDER,
            ],
        )

    def test_clone(self):
        user_1 = UserFactory.create()
        user_2 = UserFactory.create()

        experiment = ExperimentFactory.create_with_variants(
            name="great experiment",
            status=Experiment.STATUS_COMPLETE,
            short_description="This is going to be a great experiment.",
            proposed_start_date=datetime.date(2019, 4, 1),
            related_work="See also this other experiment.",
            proposed_enrollment=2,
            proposed_duration=30,
            owner=user_1,
            bugzilla_id="4455667",
            pref_type=Experiment.TYPE_ADDON,
            data_science_bugzilla_url="https://bugzilla.mozilla.org/123/",
            feature_bugzilla_url="https://bugzilla.mozilla.org/123/",
            addon_experiment_id="addon-id",
            addon_release_url="addon-url",
            archived=True,
            review_science=True,
            review_ux=True,
            firefox_min_version=Experiment.VERSION_CHOICES[1][0],
            firefox_max_version="",
            results_initial="Some great initial results.",
            results_lessons_learned="Lessons were learned.",
            results_url="http://www.example.com",
        )

        experiment.clone("best experiment", user_2)

        cloned_experiment = Experiment.objects.filter(name="best experiment").get()

        self.assertTrue(cloned_experiment.parent, experiment.id)
        self.assertIn(experiment, cloned_experiment.related_to.all())
        self.assertEqual(cloned_experiment.status, Experiment.STATUS_DRAFT)
        self.assertEqual(
            cloned_experiment.short_description, "This is going to be a great experiment."
        )
        self.assertEqual(
            cloned_experiment.related_work, "See also this other experiment."
        )
        self.assertEqual(cloned_experiment.proposed_enrollment, 2)
        self.assertEqual(cloned_experiment.proposed_duration, 30)
        self.assertEqual(cloned_experiment.pref_type, Experiment.TYPE_ADDON)
        self.assertEqual(cloned_experiment.proposed_start_date, None)
        self.assertEqual(cloned_experiment.owner, user_2)
        self.assertEqual(
            cloned_experiment.firefox_min_version, Experiment.VERSION_CHOICES[1][0]
        )
        self.assertFalse(cloned_experiment.bugzilla_id)
        self.assertFalse(cloned_experiment.archived)
        self.assertFalse(cloned_experiment.review_science)
        self.assertFalse(cloned_experiment.review_ux)
        self.assertFalse(cloned_experiment.addon_experiment_id)
        self.assertFalse(cloned_experiment.addon_release_url)
        self.assertFalse(cloned_experiment.results_lessons_learned)
        self.assertFalse(cloned_experiment.results_initial)
        self.assertFalse(cloned_experiment.results_url)

        self.assertEqual(cloned_experiment.changes.count(), 1)

        change = cloned_experiment.changes.latest()

        self.assertEqual(change.old_status, None)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


class TestVariantPreferences(TestCase):

    def setUp(self):
        super().setUp()
        self.variant = ExperimentVariantFactory.create()
        self.pref = VariantPreferences()
        self.pref.variant = self.variant
        self.pref.pref_type = Experiment.PREF_TYPE_BOOL
        self.pref.pref_value = "true"
        self.pref.pref_branch = Experiment.PREF_BRANCH_DEFAULT
        self.pref.pref_name = "pref_name"

    def test_unique_pref_name_constraint_is_violated(self):
        self.pref.save()

        pv2 = VariantPreferences()
        pv2.pref_type = Experiment.PREF_TYPE_BOOL
        pv2.pref_value = "false"
        pv2.pref_branch = Experiment.PREF_BRANCH_DEFAULT
        pv2.pref_name = "pref_name"
        pv2.variant = self.variant

        with self.assertRaises(IntegrityError):
            pv2.save()

    def test_valid_preference_are_associated_to_variant(self):

        self.pref.save()

        pv2 = VariantPreferences()
        pv2.pref_type = Experiment.PREF_TYPE_BOOL
        pv2.pref_value = "false"
        pv2.pref_branch = Experiment.PREF_BRANCH_DEFAULT
        pv2.pref_name = "pref2_name"
        pv2.variant = self.variant

        pv2.save()

        self.assertTrue(self.variant.preferences.count, 2)

    def test_valid_pref_is_able_to_update_itself(self):
        self.pref.value = 6

        self.pref.save()

        self.assertTrue(self.variant.preferences.count, 1)

    def test_is_json_string_type_returns_false(self):
        self.assertFalse(self.pref.is_json_string_type)

    def test_is_json_string_type_returns_true_for_json_string_type(self):
        self.pref.pref_type = Experiment.PREF_TYPE_JSON_STR
        self.pref.save()
        self.assertTrue(self.pref.is_json_string_type)


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

    def test_change_message(self):
        experiment = ExperimentFactory.create_with_variants()
        changelog = ExperimentChangeLogFactory.create(
            experiment=experiment,
            old_status=Experiment.STATUS_DRAFT,
            new_status=Experiment.STATUS_REVIEW,
            message="its a message!",
        )

        self.assertEqual(str(changelog), "its a message!")

    def test_pretty_status_created_draft(self):
        experiment = ExperimentFactory.create_with_variants()

        for (
            old_status,
            new_statuses,
        ) in ExperimentChangeLog.PRETTY_STATUS_LABELS.items():
            for new_status, expected_label in new_statuses.items():
                changelog = ExperimentChangeLogFactory.create(
                    experiment=experiment, old_status=old_status, new_status=new_status
                )
                self.assertEqual(changelog.pretty_status, expected_label)


class TestExperimentComments(TestCase):

    def test_manager_returns_sections(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        risk_comment = ExperimentCommentFactory.create(
            experiment=experiment, section=Experiment.SECTION_RISKS
        )
        testing_comment = ExperimentCommentFactory.create(
            experiment=experiment, section=Experiment.SECTION_TESTING
        )
        self.assertIn(
            risk_comment, experiment.comments.sections[experiment.SECTION_RISKS]
        )
        self.assertIn(
            testing_comment, experiment.comments.sections[experiment.SECTION_TESTING]
        )
        self.assertNotIn(
            risk_comment, experiment.comments.sections[experiment.SECTION_TESTING]
        )
        self.assertNotIn(
            testing_comment, experiment.comments.sections[experiment.SECTION_RISKS]
        )
