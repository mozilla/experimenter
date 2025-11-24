import datetime
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment, Tag
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    UserFactory,
    generate_nimbus_changelog,
)
from experimenter.nimbus_ui.constants import (
    APPLICATION_ICON_FILTER_TYPE,
    APPLICATION_ICON_MAP,
    CHANNEL_ICON_FILTER_TYPE,
    CHANNEL_ICON_MAP,
    QA_ICON_FILTER_TYPE,
    QA_STATUS_ICON_MAP,
    STATUS_ICON_MAP,
)
from experimenter.nimbus_ui.filtersets import (
    DateRangeChoices,
    HomeSortChoices,
    MyDeliveriesChoices,
    NimbusExperimentFilter,
)
from experimenter.nimbus_ui.templatetags.nimbus_extras import (
    application_icon_info,
    channel_icon_info,
    choices_with_icons,
    experiment_date_progress,
    format_json,
    format_not_set,
    format_string,
    home_status_display,
    qa_icon_info,
    remove_underscores,
    render_channel_icons,
    short_number,
    status_icon_info,
    to_percentage,
)
from experimenter.nimbus_ui.templatetags.nimbus_extras import (
    should_show_remote_settings_pending as filter_should_show_remote_settings_pending,
)
from experimenter.nimbus_ui.tests.test_views import AuthTestCase


class FilterTests(TestCase):
    def test_remove_underscores(self):
        self.assertEqual(remove_underscores("test_example"), "test example")
        self.assertEqual(
            remove_underscores("another_test_example"),
            "another test example",
        )

    def test_format_not_set(self):
        self.assertEqual(
            format_not_set(""),
            '<span class="text-danger">Not set</span>',
        )
        self.assertEqual(
            format_not_set(None),
            '<span class="text-danger">Not set</span>',
        )
        self.assertEqual(format_not_set("Some value"), "Some value")

    def test_format_json(self):
        input_json = '{"key": "value", "number": 123}'
        expected_output = (
            '<pre class="text-monospace" style="white-space: pre-wrap; '
            'word-wrap: break-word;">'
            '{\n  "key": "value",\n  "number": 123\n}'
            "</pre>"
        )
        result = format_json(input_json)
        self.assertEqual(result, expected_output)

        self.assertEqual(
            format_json("{key: value}"),
            '<pre class="text-monospace" '
            'style="white-space: pre-wrap; word-wrap: break-word;">'
            "{key: value}"
            "</pre>",
        )

    def test_should_show_remote_settings_pending_filter_true(self):
        reviewer = UserFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING
        )
        generate_nimbus_changelog(experiment, experiment.owner, "requested review")

        self.assertTrue(filter_should_show_remote_settings_pending(experiment, reviewer))

    def test_should_show_remote_settings_pending_filter_false_for_requester(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING
        )
        generate_nimbus_changelog(experiment, experiment.owner, "requested review")

        self.assertFalse(
            filter_should_show_remote_settings_pending(experiment, experiment.owner)
        )

    @parameterized.expand(
        [
            (NimbusExperiment.Channel.NIGHTLY,),
            (NimbusExperiment.Channel.BETA,),
            (NimbusExperiment.Channel.RELEASE,),
            (NimbusExperiment.Channel.ESR,),
            ("unknown_channel",),
        ]
    )
    def test_channel_icon_info(self, channel):
        result = channel_icon_info(channel)
        expected = CHANNEL_ICON_MAP.get(
            channel, CHANNEL_ICON_MAP[NimbusExperiment.Channel.NO_CHANNEL]
        )
        self.assertEqual(result["icon"], expected["icon"])
        self.assertEqual(result["color"], expected["color"])

    def test_short_number(self):
        self.assertEqual(short_number(100), "100")
        self.assertEqual(short_number(1000), "1.0K")
        self.assertEqual(short_number(1500), "1.5K")
        self.assertEqual(short_number(123456), "123.5K")
        self.assertEqual(short_number(510951), "511.0K")
        self.assertEqual(short_number(1000000), "1.0M")
        self.assertEqual(short_number(13500000), "13.5M")

    def test_invalid_short_number(self):
        self.assertEqual(short_number("invalid"), "invalid")
        self.assertEqual(short_number(None), "None")

    def test_format_string_with_text_placeholder(self):
        result = format_string("Subscribe to {text} for updates", "test-feature")
        self.assertEqual(result, "Subscribe to test-feature for updates")

    def test_format_string_with_multiple_placeholders(self):
        result = format_string("Feature {text} uses {text} technology", "nimbusQA")
        self.assertEqual(result, "Feature nimbusQA uses nimbusQA technology")

    def test_format_string_with_no_placeholder(self):
        result = format_string("Subscribe for updates", "Picture-in-Picture")
        self.assertEqual(result, "Subscribe for updates")

    def test_to_percentage_precision_specified(self):
        self.assertEqual(to_percentage(0.123456, 4), "12.3456%")
        self.assertEqual(to_percentage(0.123, 2), "12.30%")
        self.assertEqual(to_percentage(0.12, 0), "12%")

    def test_to_percentage_no_precision_specified(self):
        self.assertEqual(to_percentage(0.123456), "12.3456%")
        self.assertEqual(to_percentage(0.123), "12.3%")
        self.assertEqual(to_percentage(0.12), "12.0%")


class TestHomeFilters(AuthTestCase):
    def _make_all_qa_statuses(self):
        red = NimbusExperimentFactory.create(owner=self.user, qa_status="RED", name="Red")
        yellow = NimbusExperimentFactory.create(
            owner=self.user, qa_status="YELLOW", name="Yellow"
        )
        green = NimbusExperimentFactory.create(
            owner=self.user, qa_status="GREEN", name="Green"
        )
        self_red = NimbusExperimentFactory.create(
            owner=self.user, qa_status="SELF RED", name="Self Red"
        )
        self_yellow = NimbusExperimentFactory.create(
            owner=self.user, qa_status="SELF YELLOW", name="Self Yellow"
        )
        self_green = NimbusExperimentFactory.create(
            owner=self.user, qa_status="SELF GREEN", name="Self Green"
        )
        not_set = NimbusExperimentFactory.create(
            owner=self.user, qa_status="NOT SET", name="Not Set"
        )
        return red, yellow, green, self_red, self_yellow, self_green, not_set

    def _make_three_types(self):
        labs = NimbusExperimentFactory.create(
            owner=self.user,
            is_firefox_labs_opt_in=True,
            firefox_labs_title="title",
            firefox_labs_description="description",
            firefox_labs_group=NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING,
            is_rollout=False,
            name="Labs One",
        )
        rollout = NimbusExperimentFactory.create(
            owner=self.user,
            is_rollout=True,
            name="Rollout One",
        )
        experiment = NimbusExperimentFactory.create(
            owner=self.user,
            is_rollout=False,
            name="Experiment One",
        )
        return labs, rollout, experiment

    def _make_different_channels(self):
        nightly = NimbusExperimentFactory.create(
            owner=self.user,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.NIGHTLY,
            channels=[],
            name="Nightly Experiment",
        )
        beta = NimbusExperimentFactory.create(
            owner=self.user,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.BETA,
            channels=[],
            name="Beta Experiment",
        )
        release = NimbusExperimentFactory.create(
            owner=self.user,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.RELEASE,
            channels=[],
            name="Release Experiment",
        )
        multi_channel = NimbusExperimentFactory.create(
            owner=self.user,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            channels=[NimbusExperiment.Channel.BETA, NimbusExperiment.Channel.RELEASE],
            name="Multi Channel Experiment",
        )
        return nightly, beta, release, multi_channel

    def _make_different_applications(self):
        desktop_exp = NimbusExperimentFactory.create(
            owner=self.user,
            application=NimbusExperiment.Application.DESKTOP,
            name="Desktop Experiment",
        )
        fenix_exp = NimbusExperimentFactory.create(
            owner=self.user,
            application=NimbusExperiment.Application.FENIX,
            name="Fenix Experiment",
        )
        ios_exp = NimbusExperimentFactory.create(
            owner=self.user,
            application=NimbusExperiment.Application.IOS,
            name="iOS Experiment",
        )
        return desktop_exp, fenix_exp, ios_exp

    def _make_all_statuses(self):
        draft = NimbusExperimentFactory.create(
            owner=self.user,
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        preview = NimbusExperimentFactory.create(
            owner=self.user,
            status=NimbusExperiment.Status.PREVIEW,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        live = NimbusExperimentFactory.create(
            owner=self.user,
            status=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        complete = NimbusExperimentFactory.create(
            owner=self.user,
            status=NimbusExperiment.Status.COMPLETE,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )

        review = NimbusExperimentFactory.create(
            owner=self.user,
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )

        return draft, preview, live, complete, review

    def _make_different_feature_configs(self):
        feature_desktop = NimbusFeatureConfigFactory.create(
            slug="feature-desktop",
            name="Desktop Feature",
            application=NimbusExperiment.Application.DESKTOP,
        )
        feature_fenix = NimbusFeatureConfigFactory.create(
            slug="feature-fenix",
            name="Fenix Feature",
            application=NimbusExperiment.Application.FENIX,
        )
        feature_ios = NimbusFeatureConfigFactory.create(
            slug="feature-ios",
            name="iOS Feature",
            application=NimbusExperiment.Application.IOS,
        )

        exp_with_desktop_feature = NimbusExperimentFactory.create(
            owner=self.user,
            name="Experiment with Desktop Feature",
            application=NimbusExperiment.Application.DESKTOP,
        )
        exp_with_desktop_feature.feature_configs.add(feature_desktop)

        exp_with_fenix_feature = NimbusExperimentFactory.create(
            owner=self.user,
            name="Experiment with Fenix Feature",
            application=NimbusExperiment.Application.FENIX,
        )
        exp_with_fenix_feature.feature_configs.add(feature_fenix)

        exp_with_ios_feature = NimbusExperimentFactory.create(
            owner=self.user,
            name="Experiment with iOS Feature",
            application=NimbusExperiment.Application.IOS,
        )
        exp_with_ios_feature.feature_configs.add(feature_ios)

        exp_with_multiple_features = NimbusExperimentFactory.create(
            owner=self.user,
            name="Experiment with Multiple Features",
            application=NimbusExperiment.Application.DESKTOP,
        )
        exp_with_multiple_features.feature_configs.add(feature_desktop, feature_fenix)

        exp_with_no_features = NimbusExperimentFactory.create(
            owner=self.user,
            name="Experiment with No Features",
            application=NimbusExperiment.Application.DESKTOP,
        )

        return {
            "features": {
                NimbusExperiment.Application.DESKTOP: feature_desktop,
                NimbusExperiment.Application.FENIX: feature_fenix,
                NimbusExperiment.Application.IOS: feature_ios,
            },
            "experiments": {
                NimbusExperiment.Application.DESKTOP: exp_with_desktop_feature,
                NimbusExperiment.Application.FENIX: exp_with_fenix_feature,
                NimbusExperiment.Application.IOS: exp_with_ios_feature,
                "multiple": exp_with_multiple_features,
                "none": exp_with_no_features,
            },
        }

    def test_my_deliveries_status_field_is_set_to_default_initial(self):
        NimbusExperimentFactory.create(owner=self.user)

        response = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(response.status_code, 200)

        filterset = response.context.get("my_deliveries_filter")
        self.assertIsNotNone(filterset)

        field = filterset.form.fields["my_deliveries_status"]
        self.assertEqual(field.initial, MyDeliveriesChoices.ALL)

    def test_filter_returns_owned_experiments(self):
        owned_exp = NimbusExperimentFactory.create(owner=self.user)
        other_exp = NimbusExperimentFactory.create()

        response = response = self.client.get(
            f"{reverse('nimbus-ui-home')}?my_deliveries_status={MyDeliveriesChoices.OWNED}"
        )
        self.assertEqual(response.status_code, 200)

        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(owned_exp, experiments)
        self.assertNotIn(other_exp, experiments)

    def test_filter_returns_subscribed_experiments(self):
        other_user = UserFactory.create()
        subscribed_exp = NimbusExperimentFactory.create(owner=other_user)
        subscribed_exp.subscribers.add(self.user)

        not_subscribed = NimbusExperimentFactory.create()

        response = response = self.client.get(
            f"{reverse('nimbus-ui-home')}?my_deliveries_status={MyDeliveriesChoices.SUBSCRIBED}"
        )
        self.assertEqual(response.status_code, 200)

        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(subscribed_exp, experiments)
        self.assertNotIn(not_subscribed, experiments)

    def test_filter_returns_all_owned_and_subscribed_by_default(self):
        owned = NimbusExperimentFactory.create(owner=self.user)
        other_user = UserFactory.create()
        subscribed = NimbusExperimentFactory.create(owner=other_user)
        subscribed.subscribers.add(self.user)

        unrelated = NimbusExperimentFactory.create()

        response = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(response.status_code, 200)

        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(owned, experiments)
        self.assertIn(subscribed, experiments)
        self.assertNotIn(unrelated, experiments)

    def test_filter_returns_all_deliveries_experiments(self):
        owned = NimbusExperimentFactory.create(owner=self.user)
        other_user = UserFactory.create()
        subscribed = NimbusExperimentFactory.create(owner=other_user)
        subscribed.subscribers.add(self.user)

        unrelated = NimbusExperimentFactory.create()

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?my_deliveries_status={MyDeliveriesChoices.ALL}"
        )
        self.assertEqual(response.status_code, 200)

        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(owned, experiments)
        self.assertIn(subscribed, experiments)
        self.assertNotIn(unrelated, experiments)

    @parameterized.expand([(c.value,) for c in HomeSortChoices])
    def test_all_home_sort_choices_do_not_error(self, sort_value):
        NimbusExperimentFactory.create(owner=self.user, name="Sort Smoke")
        response = self.client.get(f"{reverse('nimbus-ui-home')}?sort={sort_value}")
        self.assertEqual(response.status_code, 200)

    @parameterized.expand(
        [
            (HomeSortChoices.NAME_UP, HomeSortChoices.NAME_DOWN),
            (HomeSortChoices.APPLICATION_UP, HomeSortChoices.APPLICATION_DOWN),
            (HomeSortChoices.TYPE_UP, HomeSortChoices.TYPE_DOWN),
            (HomeSortChoices.CHANNEL_UP, HomeSortChoices.CHANNEL_DOWN),
            (HomeSortChoices.SIZE_UP, HomeSortChoices.SIZE_DOWN),
        ]
    )
    def test_sorting_changes_first_row_for_choice(self, sort_up, sort_down):
        low = NimbusExperimentFactory.create(
            owner=self.user,
            name="A Low",
            application=NimbusExperiment.Application.FENIX,
            is_rollout=False,
            channel=NimbusExperiment.Channel.BETA,
            channels=[],
            population_percent=5,
            firefox_min_version=120,
        )
        high = NimbusExperimentFactory.create(
            owner=self.user,
            name="Z High",
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            channels=[NimbusExperiment.Channel.RELEASE],
            population_percent=50,
            firefox_min_version=130,
        )
        resp = self.client.get(f"{reverse('nimbus-ui-home')}?sort={sort_up.value}")
        self.assertEqual(resp.status_code, 200)
        page = resp.context["all_my_experiments_page"].object_list
        self.assertGreaterEqual(len(page), 2)
        self.assertEqual(page[0].id, low.id, f"{sort_up} should surface 'low'")

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?sort={sort_down.value}")
        self.assertEqual(resp.status_code, 200)
        page = resp.context["all_my_experiments_page"].object_list
        self.assertGreaterEqual(len(page), 2)
        self.assertEqual(page[0].id, high.id, f"{sort_down} should surface 'high'")

    def test_sorting_by_versions(self):
        experiment_95 = NimbusExperimentFactory.create(
            owner=self.user,
            slug="firefox-95",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_95,
        )
        experiment_100 = NimbusExperimentFactory.create(
            owner=self.user,
            slug="firefox-100",
            firefox_min_version=NimbusExperiment.Version.FIREFOX_100,
        )
        experiment_no_version = NimbusExperimentFactory.create(
            owner=self.user,
            slug="no-version",
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
        )

        resp = self.client.get(
            f"{reverse('nimbus-ui-home')}?sort={HomeSortChoices.VERSIONS_UP.value}"
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            [e.slug for e in resp.context["all_my_experiments_page"].object_list],
            [experiment_no_version.slug, experiment_95.slug, experiment_100.slug],
        )

        resp = self.client.get(
            f"{reverse('nimbus-ui-home')}?sort={HomeSortChoices.VERSIONS_DOWN.value}"
        )
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            [e.slug for e in resp.context["all_my_experiments_page"].object_list],
            [experiment_100.slug, experiment_95.slug, experiment_no_version.slug],
        )

    def test_sorting_by_dates_uses_start_date(self):
        older = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=datetime.date(2024, 1, 1),
            owner=self.user,
        )
        newer = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=datetime.date(2024, 1, 2),
            owner=self.user,
        )
        resp = self.client.get(
            f"{reverse('nimbus-ui-home')}?sort={HomeSortChoices.DATES_UP.value}"
        )
        self.assertEqual(resp.status_code, 200)
        page = resp.context["all_my_experiments_page"].object_list
        self.assertEqual(page[0].id, older.id)

        resp = self.client.get(
            f"{reverse('nimbus-ui-home')}?sort={HomeSortChoices.DATES_DOWN.value}"
        )
        self.assertEqual(resp.status_code, 200)
        page = resp.context["all_my_experiments_page"].object_list
        self.assertEqual(page[0].id, newer.id)

    def test_sorting_by_features_slug(self):
        feat_a = NimbusFeatureConfigFactory.create(slug="aaa")
        feat_z = NimbusFeatureConfigFactory.create(slug="zzz")

        low = NimbusExperimentFactory.create(owner=self.user, name="Feat Low")
        high = NimbusExperimentFactory.create(owner=self.user, name="Feat High")
        low.feature_configs.add(feat_a)
        high.feature_configs.add(feat_z)

        resp = self.client.get(
            f"{reverse('nimbus-ui-home')}?sort={HomeSortChoices.FEATURES_UP.value}"
        )
        self.assertEqual(resp.status_code, 200)
        page = resp.context["all_my_experiments_page"].object_list
        self.assertEqual(page[0].id, low.id)

        resp = self.client.get(
            f"{reverse('nimbus-ui-home')}?sort={HomeSortChoices.FEATURES_DOWN.value}"
        )
        self.assertEqual(resp.status_code, 200)
        page = resp.context["all_my_experiments_page"].object_list
        self.assertEqual(page[0].id, high.id)

    def _assert_page_membership(self, resp, includes, excludes):
        page = list(resp.context["all_my_experiments_page"].object_list)
        for obj in includes:
            self.assertIn(obj, page)
        for obj in excludes:
            self.assertNotIn(obj, page)

    @parameterized.expand(
        [
            ("labs_only", "type=Labs", ["labs"], ["rollout", "experiment"]),
            ("rollout_only", "type=Rollout", ["rollout"], ["labs", "experiment"]),
            ("experiment_only", "type=Experiment", ["experiment"], ["labs", "rollout"]),
            (
                "labs_and_rollout",
                "type=Labs&type=Rollout",
                ["labs", "rollout"],
                ["experiment"],
            ),
        ]
    )
    def test_filter_type(self, name, querystring, expected_in, expected_not_in):
        labs, rollout, experiment = self._make_three_types()
        mapping = {"labs": labs, "rollout": rollout, "experiment": experiment}

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?{querystring}")
        self.assertEqual(resp.status_code, 200)

        includes = [mapping[k] for k in expected_in]
        excludes = [mapping[k] for k in expected_not_in]
        self._assert_page_membership(resp, includes, excludes)

    def test_filter_type_with_sort_preserved(self):
        labs, rollout, experiment = self._make_three_types()

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?type=Labs&sort=name")
        self.assertEqual(resp.status_code, 200)

        page = list(resp.context["all_my_experiments_page"].object_list)
        self.assertEqual(page, [labs])

    @parameterized.expand(
        [
            (
                "red_only",
                "qa_status=RED",
                ["red"],
                ["yellow", "green", "self_red", "self_yellow", "self_green", "not_set"],
            ),
            (
                "yellow_only",
                "qa_status=YELLOW",
                ["yellow"],
                ["red", "green", "self_red", "self_yellow", "self_green", "not_set"],
            ),
            (
                "green_only",
                "qa_status=GREEN",
                ["green"],
                ["red", "yellow", "self_red", "self_yellow", "self_green", "not_set"],
            ),
            (
                "self_red_only",
                "qa_status=SELF RED",
                ["self_red"],
                ["red", "yellow", "green", "self_yellow", "self_green", "not_set"],
            ),
            (
                "self_yellow_only",
                "qa_status=SELF YELLOW",
                ["self_yellow"],
                ["red", "yellow", "green", "self_red", "self_green", "not_set"],
            ),
            (
                "self_green_only",
                "qa_status=SELF GREEN",
                ["self_green"],
                ["red", "yellow", "green", "self_red", "self_yellow", "not_set"],
            ),
            (
                "not_set_only",
                "qa_status=NOT SET",
                ["not_set"],
                ["red", "yellow", "green", "self_red", "self_yellow", "self_green"],
            ),
            (
                "red_and_yellow",
                "qa_status=RED&qa_status=YELLOW",
                ["red", "yellow"],
                ["green", "self_red", "self_yellow", "self_green", "not_set"],
            ),
        ]
    )
    def test_filter_qa_status(self, name, querystring, expected_in, expected_not_in):
        red, yellow, green, self_red, self_yellow, self_green, not_set = (
            self._make_all_qa_statuses()
        )
        mapping = {
            "red": red,
            "yellow": yellow,
            "green": green,
            "self_red": self_red,
            "self_yellow": self_yellow,
            "self_green": self_green,
            "not_set": not_set,
        }

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?{querystring}")
        self.assertEqual(resp.status_code, 200)

        includes = [mapping[k] for k in expected_in]
        excludes = [mapping[k] for k in expected_not_in]
        self._assert_page_membership(resp, includes, excludes)

    @parameterized.expand(
        [
            (
                "nightly_only",
                f"channel={NimbusExperiment.Channel.NIGHTLY}",
                [NimbusExperiment.Channel.NIGHTLY],
                [
                    NimbusExperiment.Channel.BETA,
                    NimbusExperiment.Channel.RELEASE,
                    "multi_channel",
                ],
            ),
            (
                "beta_only",
                f"channel={NimbusExperiment.Channel.BETA}",
                [NimbusExperiment.Channel.BETA, "multi_channel"],
                [NimbusExperiment.Channel.NIGHTLY, NimbusExperiment.Channel.RELEASE],
            ),
            (
                "release_only",
                f"channel={NimbusExperiment.Channel.RELEASE}",
                [NimbusExperiment.Channel.RELEASE, "multi_channel"],
                [NimbusExperiment.Channel.NIGHTLY, NimbusExperiment.Channel.BETA],
            ),
            (
                "nightly_and_beta",
                f"channel={NimbusExperiment.Channel.NIGHTLY}"
                f"&channel={NimbusExperiment.Channel.BETA}",
                [
                    NimbusExperiment.Channel.NIGHTLY,
                    NimbusExperiment.Channel.BETA,
                    "multi_channel",
                ],
                [NimbusExperiment.Channel.RELEASE],
            ),
        ]
    )
    def test_filter_channel(self, name, querystring, expected_in, expected_not_in):
        nightly, beta, release, multi_channel = self._make_different_channels()
        mapping = {
            NimbusExperiment.Channel.NIGHTLY: nightly,
            NimbusExperiment.Channel.BETA: beta,
            NimbusExperiment.Channel.RELEASE: release,
            "multi_channel": multi_channel,
        }

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?{querystring}")
        self.assertEqual(resp.status_code, 200)

        includes = [mapping[k] for k in expected_in]
        excludes = [mapping[k] for k in expected_not_in]
        self._assert_page_membership(resp, includes, excludes)

    @parameterized.expand(
        [
            (
                "desktop_only",
                f"application={NimbusExperiment.Application.DESKTOP}",
                [NimbusExperiment.Application.DESKTOP],
                [NimbusExperiment.Application.FENIX, NimbusExperiment.Application.IOS],
            ),
            (
                "fenix_only",
                f"application={NimbusExperiment.Application.FENIX}",
                [NimbusExperiment.Application.FENIX],
                [NimbusExperiment.Application.DESKTOP, NimbusExperiment.Application.IOS],
            ),
            (
                "ios_only",
                f"application={NimbusExperiment.Application.IOS}",
                [NimbusExperiment.Application.IOS],
                [
                    NimbusExperiment.Application.DESKTOP,
                    NimbusExperiment.Application.FENIX,
                ],
            ),
            (
                "desktop_and_fenix",
                f"application={NimbusExperiment.Application.DESKTOP}"
                f"&application={NimbusExperiment.Application.FENIX}",
                [
                    NimbusExperiment.Application.DESKTOP,
                    NimbusExperiment.Application.FENIX,
                ],
                [NimbusExperiment.Application.IOS],
            ),
        ]
    )
    def test_filter_application(self, name, querystring, expected_in, expected_not_in):
        desktop, fenix, ios = self._make_different_applications()
        mapping = {
            NimbusExperiment.Application.DESKTOP: desktop,
            NimbusExperiment.Application.FENIX: fenix,
            NimbusExperiment.Application.IOS: ios,
        }

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?{querystring}")
        self.assertEqual(resp.status_code, 200)

        includes = [mapping[k] for k in expected_in]
        excludes = [mapping[k] for k in expected_not_in]
        self._assert_page_membership(resp, includes, excludes)

    @parameterized.expand(
        [
            (
                "draft_only",
                f"status={NimbusExperiment.Status.DRAFT}",
                [NimbusExperiment.Status.DRAFT],
                [
                    NimbusExperiment.Status.PREVIEW,
                    NimbusExperiment.Status.LIVE,
                    NimbusExperiment.Status.COMPLETE,
                    NimbusExperiment.PublishStatus.REVIEW,
                ],
            ),
            (
                "preview_only",
                f"status={NimbusExperiment.Status.PREVIEW}",
                [NimbusExperiment.Status.PREVIEW],
                [
                    NimbusExperiment.Status.DRAFT,
                    NimbusExperiment.Status.LIVE,
                    NimbusExperiment.Status.COMPLETE,
                    NimbusExperiment.PublishStatus.REVIEW,
                ],
            ),
            (
                "live_only",
                f"status={NimbusExperiment.Status.LIVE}",
                [NimbusExperiment.Status.LIVE],
                [
                    NimbusExperiment.Status.DRAFT,
                    NimbusExperiment.Status.PREVIEW,
                    NimbusExperiment.Status.COMPLETE,
                    NimbusExperiment.PublishStatus.REVIEW,
                ],
            ),
            (
                "complete_only",
                f"status={NimbusExperiment.Status.COMPLETE}",
                [NimbusExperiment.Status.COMPLETE],
                [
                    NimbusExperiment.Status.DRAFT,
                    NimbusExperiment.Status.PREVIEW,
                    NimbusExperiment.Status.LIVE,
                    NimbusExperiment.PublishStatus.REVIEW,
                ],
            ),
            (
                "review_only",
                f"status={NimbusExperiment.PublishStatus.REVIEW}",
                [NimbusExperiment.PublishStatus.REVIEW],
                [
                    NimbusExperiment.Status.DRAFT,
                    NimbusExperiment.Status.PREVIEW,
                    NimbusExperiment.Status.LIVE,
                    NimbusExperiment.Status.COMPLETE,
                ],
            ),
        ]
    )
    def test_filter_status(
        self, name, querystring, expected_in_statuses, expected_not_in_statuses
    ):
        draft, preview, live, complete, review = self._make_all_statuses()

        status_to_experiment = {
            NimbusExperiment.Status.DRAFT: draft,
            NimbusExperiment.Status.PREVIEW: preview,
            NimbusExperiment.Status.LIVE: live,
            NimbusExperiment.Status.COMPLETE: complete,
            NimbusExperiment.PublishStatus.REVIEW: review,
        }

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?{querystring}")
        self.assertEqual(resp.status_code, 200)

        includes = [status_to_experiment[status] for status in expected_in_statuses]
        excludes = [status_to_experiment[status] for status in expected_not_in_statuses]
        self._assert_page_membership(resp, includes, excludes)

    @parameterized.expand(
        [
            (
                "desktop_feature",
                NimbusExperiment.Application.DESKTOP,
                [NimbusExperiment.Application.DESKTOP, "multiple"],
                [
                    NimbusExperiment.Application.FENIX,
                    NimbusExperiment.Application.IOS,
                    "none",
                ],
            ),
            (
                "fenix_feature",
                NimbusExperiment.Application.FENIX,
                [NimbusExperiment.Application.FENIX, "multiple"],
                [
                    NimbusExperiment.Application.DESKTOP,
                    NimbusExperiment.Application.IOS,
                    "none",
                ],
            ),
            (
                "ios_feature",
                NimbusExperiment.Application.IOS,
                [NimbusExperiment.Application.IOS],
                [
                    NimbusExperiment.Application.DESKTOP,
                    NimbusExperiment.Application.FENIX,
                    "multiple",
                    "none",
                ],
            ),
        ]
    )
    def test_filter_feature_configs_single_feature(
        self, name, feature_key, expected_in_keys, expected_not_in_keys
    ):
        test_data = self._make_different_feature_configs()
        features = test_data["features"]
        experiments = test_data["experiments"]

        feature_id = features[feature_key].id
        resp = self.client.get(
            f"{reverse('nimbus-ui-home')}?feature_configs={feature_id}"
        )
        self.assertEqual(resp.status_code, 200)

        includes = [experiments[key] for key in expected_in_keys]
        excludes = [experiments[key] for key in expected_not_in_keys]
        self._assert_page_membership(resp, includes, excludes)

    def test_filter_feature_configs_returns_all_by_default(self):
        test_data = self._make_different_feature_configs()
        experiments = test_data["experiments"]

        resp = self.client.get(reverse("nimbus-ui-home"))
        self.assertEqual(resp.status_code, 200)

        all_experiments = list(experiments.values())
        self._assert_page_membership(resp, all_experiments, [])

    def test_home_status_display_filter(self):
        draft, preview, live, complete, review = self._make_all_statuses()

        self.assertEqual(home_status_display(draft), NimbusExperiment.Status.DRAFT)
        self.assertEqual(home_status_display(preview), NimbusExperiment.Status.PREVIEW)
        self.assertEqual(home_status_display(live), NimbusExperiment.Status.LIVE)
        self.assertEqual(home_status_display(complete), NimbusExperiment.Status.COMPLETE)
        self.assertEqual(
            home_status_display(review), NimbusExperiment.PublishStatus.REVIEW
        )

        archived = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_archived=True,
        )
        self.assertEqual(home_status_display(archived), NimbusConstants.Status.DRAFT)

    @parameterized.expand(
        [
            (
                "draft_status",
                NimbusConstants.Status.DRAFT,
                NimbusConstants.Status.DRAFT,
            ),
            (
                "preview_status",
                NimbusConstants.Status.PREVIEW,
                NimbusConstants.Status.PREVIEW,
            ),
            (
                "live_status",
                NimbusConstants.Status.LIVE,
                NimbusConstants.Status.LIVE,
            ),
            (
                "complete_status",
                NimbusConstants.Status.COMPLETE,
                NimbusConstants.Status.COMPLETE,
            ),
            (
                "review_status",
                NimbusConstants.PublishStatus.REVIEW,
                NimbusConstants.PublishStatus.REVIEW,
            ),
        ]
    )
    def test_home_status_display_with_icon_filter(
        self, name, status_constant, expected_status
    ):
        from experimenter.nimbus_ui.templatetags.nimbus_extras import (
            home_status_display_with_icon,
        )

        draft, preview, live, complete, review = self._make_all_statuses()
        status_to_experiment = {
            NimbusConstants.Status.DRAFT: draft,
            NimbusConstants.Status.PREVIEW: preview,
            NimbusConstants.Status.LIVE: live,
            NimbusConstants.Status.COMPLETE: complete,
            NimbusConstants.PublishStatus.REVIEW: review,
        }

        experiment = status_to_experiment[status_constant]
        result = home_status_display_with_icon(experiment)

        self.assertEqual(result["status"], expected_status)
        self.assertIn("icon", result["icon_info"])
        self.assertIn("color", result["icon_info"])
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("icon_info", result)

    @parameterized.expand(
        [
            (
                "single_channel_with_icon",
                {
                    "application": NimbusExperiment.Application.FENIX,
                    "channel": NimbusExperiment.Channel.NIGHTLY,
                    "channels": [],
                },
                1,
                "Nightly",
                False,
            ),
            (
                "multi_channel_with_icons",
                {
                    "application": NimbusExperiment.Application.DESKTOP,
                    "channel": NimbusExperiment.Channel.NO_CHANNEL,
                    "channels": [
                        NimbusExperiment.Channel.BETA,
                        NimbusExperiment.Channel.RELEASE,
                    ],
                },
                2,
                None,
                True,
            ),
            (
                "no_channels",
                {
                    "channel": NimbusExperiment.Channel.NO_CHANNEL,
                    "channels": [],
                },
                0,
                None,
                None,
            ),
        ]
    )
    def test_render_channel_icons(
        self, name, experiment_kwargs, expected_count, expected_label, is_multi
    ):
        experiment = NimbusExperimentFactory.create(**experiment_kwargs)
        result = render_channel_icons(experiment)

        self.assertEqual(len(result), expected_count)

        if expected_count > 0:
            for channel_data in result:
                self.assertIn("icon_info", channel_data)
                self.assertIn("label", channel_data)
                self.assertIn("is_multi", channel_data)
                self.assertIn("icon", channel_data["icon_info"])
                self.assertIn("color", channel_data["icon_info"])

            if expected_label:
                self.assertEqual(result[0]["label"], expected_label)
                self.assertEqual(result[0]["is_multi"], is_multi)
            elif is_multi is not None:
                self.assertTrue(all(channel["is_multi"] for channel in result))
                labels = [channel["label"] for channel in result]
                self.assertIn("Beta", labels)
                self.assertIn("Release", labels)

    @parameterized.expand(
        [
            (NimbusExperiment.Channel.NIGHTLY,),
            (NimbusExperiment.Channel.BETA,),
            (NimbusExperiment.Channel.RELEASE,),
            (NimbusExperiment.Channel.ESR,),
        ]
    )
    def test_channel_icon_info_filter(self, channel):
        result = channel_icon_info(channel)
        expected = NimbusExperiment.Channel.get_icon_info(channel)
        self.assertEqual(result["icon"], expected["icon"])
        self.assertEqual(result["color"], expected["color"])

    @parameterized.expand(
        [
            (NimbusConstants.QAStatus.RED,),
            (NimbusConstants.QAStatus.YELLOW,),
            (NimbusConstants.QAStatus.GREEN,),
            (NimbusConstants.QAStatus.SELF_RED,),
            (NimbusConstants.QAStatus.SELF_YELLOW,),
            (NimbusConstants.QAStatus.SELF_GREEN,),
            (NimbusConstants.QAStatus.NOT_SET,),
        ]
    )
    def test_qa_icon_info_filter(self, qa_status):
        result = qa_icon_info(qa_status)
        expected = QA_STATUS_ICON_MAP.get(
            qa_status, QA_STATUS_ICON_MAP[NimbusConstants.QAStatus.NOT_SET]
        )
        self.assertEqual(result["icon"], expected["icon"])
        self.assertEqual(result["color"], expected["color"])

    def test_choices_with_icons_qa_filter(self):
        choices = [
            (NimbusConstants.QAStatus.GREEN, "Green"),
            (NimbusConstants.QAStatus.RED, "Red"),
        ]

        result = choices_with_icons(choices, QA_ICON_FILTER_TYPE)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["value"], NimbusConstants.QAStatus.GREEN)
        self.assertEqual(result[0]["label"], "Green")
        self.assertIn("icon_info", result[0])
        self.assertEqual(
            result[0]["icon_info"]["icon"],
            QA_STATUS_ICON_MAP[NimbusConstants.QAStatus.GREEN]["icon"],
        )

    def test_choices_with_icons_channel_filter(self):
        choices = [
            (NimbusExperiment.Channel.NIGHTLY, "Nightly"),
            (NimbusExperiment.Channel.BETA, "Beta"),
        ]

        result = choices_with_icons(choices, CHANNEL_ICON_FILTER_TYPE)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["value"], NimbusExperiment.Channel.NIGHTLY)
        self.assertEqual(result[0]["label"], "Nightly")
        self.assertIn("icon_info", result[0])
        self.assertEqual(
            result[0]["icon_info"]["icon"],
            CHANNEL_ICON_MAP[NimbusExperiment.Channel.NIGHTLY]["icon"],
        )

    def test_choices_with_icons_unknown_filter(self):
        choices = [
            ("value1", "Label 1"),
            ("value2", "Label 2"),
        ]

        result = choices_with_icons(choices, "unknown_filter")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["value"], "value1")
        self.assertEqual(result[0]["label"], "Label 1")
        self.assertIsNone(result[0]["icon_info"])

    @parameterized.expand(
        [
            (NimbusExperiment.Application.DESKTOP,),
            (NimbusExperiment.Application.FENIX,),
            (NimbusExperiment.Application.IOS,),
            (NimbusExperiment.Application.FOCUS_ANDROID,),
            (NimbusExperiment.Application.KLAR_ANDROID,),
            (NimbusExperiment.Application.FOCUS_IOS,),
            (NimbusExperiment.Application.KLAR_IOS,),
            (NimbusExperiment.Application.MONITOR,),
            (NimbusExperiment.Application.VPN,),
            (NimbusExperiment.Application.FXA,),
            (NimbusExperiment.Application.DEMO_APP,),
            (NimbusExperiment.Application.EXPERIMENTER,),
        ]
    )
    def test_application_icon_info_filter(self, application):
        result = application_icon_info(application)
        expected = APPLICATION_ICON_MAP.get(
            application, APPLICATION_ICON_MAP[NimbusExperiment.Application.DESKTOP]
        )
        self.assertEqual(result["icon"], expected["icon"])
        self.assertEqual(result["color"], expected["color"])

    def test_choices_with_icons_application_filter(self):
        choices = [
            (NimbusExperiment.Application.DESKTOP, "Desktop"),
            (NimbusExperiment.Application.FENIX, "Fenix"),
        ]

        result = choices_with_icons(choices, APPLICATION_ICON_FILTER_TYPE)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["value"], NimbusExperiment.Application.DESKTOP)
        self.assertEqual(result[0]["label"], "Desktop")
        self.assertIn("icon_info", result[0])
        self.assertEqual(
            result[0]["icon_info"]["icon"],
            APPLICATION_ICON_MAP[NimbusExperiment.Application.DESKTOP]["icon"],
        )

    @parameterized.expand(
        [
            (NimbusConstants.Status.DRAFT,),
            (NimbusConstants.Status.PREVIEW,),
            (NimbusConstants.Status.LIVE,),
            (NimbusConstants.Status.COMPLETE,),
            (NimbusConstants.PublishStatus.REVIEW,),
        ]
    )
    def test_status_icon_info_filter(self, status):
        result = status_icon_info(status)
        expected = STATUS_ICON_MAP.get(status, {"icon": "", "color": ""})
        self.assertEqual(result["icon"], expected["icon"])
        self.assertEqual(result["color"], expected["color"])

    def test_status_icon_info_filter_unknown_status(self):
        # Test the default case when status is not found in STATUS_ICON_MAP
        result = status_icon_info("unknown_status")
        self.assertEqual(result["icon"], "")
        self.assertEqual(result["color"], "")

    @parameterized.expand(
        [
            (
                "draft_na",
                NimbusExperimentFactory.Lifecycles.CREATED,
                False,
                "",
                "N/A",
                False,
                False,
                True,
                False,
            ),
            (
                "preview_na",
                NimbusExperimentFactory.Lifecycles.PREVIEW,
                False,
                "",
                "N/A",
                False,
                False,
                True,
                False,
            ),
            (
                "review_na",
                NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_WAITING,
                False,
                "",
                "N/A",
                False,
                False,
                True,
                False,
            ),
        ]
    )
    def test_experiment_date_progress_na_states(
        self,
        test_name,
        lifecycle_state,
        expected_show_bar,
        expected_bar_class,
        expected_days_text,
        expected_is_overdue,
        expected_is_complete,
        expected_is_na,
        expected_has_alert,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(lifecycle_state)
        result = experiment_date_progress(experiment)

        self.assertEqual(result["show_bar"], expected_show_bar)
        self.assertEqual(result["bar_class"], expected_bar_class)
        self.assertEqual(result["days_text"], expected_days_text)
        self.assertEqual(result["is_overdue"], expected_is_overdue)
        self.assertEqual(result["is_complete"], expected_is_complete)
        self.assertEqual(result["is_na"], expected_is_na)
        self.assertEqual(result["has_alert"], expected_has_alert)

    def test_experiment_date_progress_completed_state(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            start_date=datetime.date.today() - timedelta(days=5),
            end_date=datetime.date.today() - timedelta(days=3),
            proposed_duration=15,
            proposed_enrollment=10,
        )
        result = experiment_date_progress(experiment)

        self.assertTrue(result["show_bar"])
        self.assertEqual(result["bar_class"], "bg-secondary")
        self.assertEqual(result["days_text"], "Complete")
        self.assertFalse(result["is_overdue"])
        self.assertTrue(result["is_complete"])
        self.assertFalse(result["is_na"])
        self.assertFalse(result["has_alert"])

    @parameterized.expand(
        [
            (
                "enrolling_early",
                3,
                12,
                15,
                10,
                (15, 25),
            ),
            (
                "enrolling_mid",
                8,
                7,
                15,
                10,
                (45, 65),
            ),
            (
                "enrolling_late",
                12,
                3,
                15,
                10,
                (75, 85),
            ),
        ]
    )
    def test_experiment_date_progress_live_enrolling(
        self,
        test_name,
        start_days_ago,
        end_days_from_now,
        proposed_duration,
        proposed_enrollment,
        expected_progress_range,
    ):
        start_date = datetime.date.today() - timedelta(days=start_days_ago)
        end_date = datetime.date.today() + timedelta(days=end_days_from_now)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=start_date,
            end_date=end_date,
            proposed_duration=proposed_duration,
            proposed_enrollment=proposed_enrollment,
        )
        result = experiment_date_progress(experiment)

        self.assertTrue(result["show_bar"])
        self.assertEqual(result["bar_class"], "bg-success")
        self.assertIn("days", result["days_text"])
        self.assertFalse(result["is_overdue"])
        self.assertFalse(result["is_complete"])
        self.assertFalse(result["is_na"])
        self.assertFalse(result["has_alert"])

        min_progress, max_progress = expected_progress_range
        self.assertGreaterEqual(result["progress_percentage"], min_progress)
        self.assertLessEqual(result["progress_percentage"], max_progress)

    @parameterized.expand(
        [
            (
                "paused_early",
                4,
                16,
                20,
                8,
                (30, 40),
            ),
            (
                "paused_mid",
                10,
                10,
                20,
                8,
                (80, 90),
            ),
            (
                "paused_late",
                8,
                4,
                20,
                8,
                (65, 75),
            ),
        ]
    )
    def test_experiment_date_progress_live_paused(
        self,
        test_name,
        start_days_ago,
        end_days_from_now,
        proposed_duration,
        proposed_enrollment,
        expected_progress_range,
    ):
        start_date = datetime.date.today() - timedelta(days=start_days_ago)
        end_date = datetime.date.today() + timedelta(days=end_days_from_now)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_PAUSED,
            start_date=start_date,
            end_date=end_date,
            proposed_duration=proposed_duration,
            proposed_enrollment=proposed_enrollment,
        )
        result = experiment_date_progress(experiment)

        self.assertTrue(result["show_bar"])
        self.assertEqual(result["bar_class"], "bg-info")
        self.assertIn("days", result["days_text"])
        self.assertFalse(result["is_overdue"])
        self.assertFalse(result["is_complete"])
        self.assertFalse(result["is_na"])
        self.assertFalse(result["has_alert"])

        min_progress, max_progress = expected_progress_range
        self.assertGreaterEqual(result["progress_percentage"], min_progress)
        self.assertLessEqual(result["progress_percentage"], max_progress)

    @parameterized.expand(
        [
            (
                "overdue_enrolling",
                NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
                20,
                -5,
                15,
                10,
            ),
            (
                "overdue_paused",
                NimbusExperimentFactory.Lifecycles.LIVE_PAUSED,
                25,
                -3,
                20,
                8,
            ),
        ]
    )
    def test_experiment_date_progress_overdue(
        self,
        test_name,
        lifecycle_state,
        start_days_ago,
        end_days_from_now,
        proposed_duration,
        proposed_enrollment,
    ):
        start_date = datetime.date.today() - timedelta(days=start_days_ago)
        end_date = datetime.date.today() + timedelta(days=end_days_from_now)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            lifecycle_state,
            start_date=start_date,
            end_date=end_date,
            proposed_duration=proposed_duration,
            proposed_enrollment=proposed_enrollment,
        )
        result = experiment_date_progress(experiment)

        self.assertTrue(result["show_bar"])
        self.assertEqual(result["bar_class"], "bg-danger")
        self.assertTrue(result["days_text"].startswith("-"))
        self.assertTrue(result["is_overdue"])
        self.assertFalse(result["is_complete"])
        self.assertFalse(result["is_na"])
        self.assertTrue(result["has_alert"])

    def test_experiment_date_progress_cross_year_formatting(self):
        last_year = datetime.date.today().replace(year=datetime.date.today().year - 1)
        next_year = datetime.date.today().replace(year=datetime.date.today().year + 1)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=last_year,
            end_date=next_year,
            proposed_duration=730,
            proposed_enrollment=30,
        )
        result = experiment_date_progress(experiment)

        current_year = datetime.date.today().year
        self.assertIn(str(current_year - 1), result["date_range_text"])
        self.assertIn(str(current_year + 1), result["date_range_text"])
        self.assertIn(",", result["date_range_text"])

    def test_experiment_date_progress_zero_duration_fallback(self):
        start_date = datetime.date.today()
        end_date = datetime.date.today() + timedelta(days=2)

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=start_date,
            end_date=end_date,
            proposed_duration=0,
            proposed_enrollment=0,
        )
        result = experiment_date_progress(experiment)

        self.assertTrue(result["show_bar"])
        self.assertEqual(result["bar_class"], "bg-success")
        self.assertIn("days", result["days_text"])
        self.assertGreaterEqual(result["progress_percentage"], 0)
        self.assertLessEqual(result["progress_percentage"], 100)

    def test_experiment_date_progress_required_keys(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_ENROLLING,
            start_date=datetime.date.today() - timedelta(days=5),
            end_date=datetime.date.today() + timedelta(days=10),
        )
        result = experiment_date_progress(experiment)

        required_keys = [
            "show_bar",
            "bar_class",
            "bar_style",
            "days_text",
            "progress_percentage",
            "is_overdue",
            "is_complete",
            "is_na",
            "has_alert",
            "start_date",
            "end_date",
            "date_range_text",
        ]
        for key in required_keys:
            self.assertIn(key, result)

    @parameterized.expand(
        [
            (
                "last_7_days",
                DateRangeChoices.LAST_7_DAYS,
                5,  # experiment from 5 days ago should be included
                15,  # experiment from 15 days ago should be excluded
            ),
            (
                "last_30_days",
                DateRangeChoices.LAST_30_DAYS,
                25,  # experiment from 25 days ago should be included
                45,  # experiment from 45 days ago should be excluded
            ),
            (
                "last_3_months",
                DateRangeChoices.LAST_3_MONTHS,
                80,  # experiment from 80 days ago should be included
                100,  # experiment from 100 days ago should be excluded
            ),
            (
                "last_6_months",
                DateRangeChoices.LAST_6_MONTHS,
                170,  # experiment from 170 days ago should be included
                200,  # experiment from 200 days ago should be excluded
            ),
        ]
    )
    def test_date_range_filter_predefined_ranges(
        self, name, date_range_choice, included_days_ago, excluded_days_ago
    ):
        today = date.today()

        included_exp = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=today - timedelta(days=included_days_ago),
            name=f"Included Experiment - {included_days_ago} days ago",
        )
        excluded_exp = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=today - timedelta(days=excluded_days_ago),
            name=f"Excluded Experiment - {excluded_days_ago} days ago",
        )

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?date_range={date_range_choice}"
        )
        self.assertEqual(response.status_code, 200)

        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(included_exp, experiments)
        self.assertNotIn(excluded_exp, experiments)

    @parameterized.expand(
        [
            (
                "start_date_only",
                {"start_date": "2024-01-01"},  # Filter from Jan 1, 2024
                {
                    "_start_date": date(2024, 2, 1)
                },  # Should be included (after start date)
                {
                    "_start_date": date(2023, 12, 1)
                },  # Should be excluded (before start date)
            ),
            (
                "end_date_only",
                {"end_date": "2024-06-01"},  # Filter until June 1, 2024
                {
                    "_start_date": date(2024, 1, 1),
                    "_computed_end_date": date(2024, 5, 1),
                },  # Should be included (ends before)
                {
                    "_start_date": date(2024, 1, 1),
                    "_computed_end_date": date(2024, 7, 1),
                },  # Should be excluded (ends after)
            ),
            (
                "both_dates",
                {
                    "start_date": "2024-01-01",
                    "end_date": "2024-06-01",
                },  # Range: Jan-June 2024
                {
                    "_start_date": date(2024, 2, 1),
                    "_computed_end_date": date(2024, 5, 1),
                },  # Should be included (within range)
                {
                    "_start_date": date(2023, 12, 1),
                    "_computed_end_date": date(2024, 3, 1),
                },  # Should be excluded (starts before)
            ),
            (
                "future_dates",
                {"start_date": "2025-01-01"},  # Future start date
                {
                    "_start_date": date(2025, 2, 1)
                },  # Should be included (future experiment)
                {
                    "_start_date": date(2024, 6, 1)
                },  # Should be excluded (current experiment)
            ),
            (
                "no_custom_dates",
                {},  # No dates provided with custom range
                {"_start_date": date(2024, 1, 1)},  # Should be included (all experiments)
                {},  # All experiments included, so no exclusions
            ),
        ]
    )
    def test_date_range_filter_custom_ranges(
        self, name, date_params, included_exp_kwargs, excluded_exp_kwargs
    ):
        included_exp = NimbusExperimentFactory.create(
            owner=self.user, name=f"Included Experiment - {name}", **included_exp_kwargs
        )
        excluded_exp = None
        if excluded_exp_kwargs:
            excluded_exp = NimbusExperimentFactory.create(
                owner=self.user,
                name=f"Excluded Experiment - {name}",
                **excluded_exp_kwargs,
            )

        query_params = {"date_range": DateRangeChoices.CUSTOM}
        query_params.update(date_params)

        query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
        response = self.client.get(f"{reverse('nimbus-ui-home')}?{query_string}")
        self.assertEqual(response.status_code, 200)

        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(included_exp, experiments)

        if excluded_exp:
            self.assertNotIn(excluded_exp, experiments)

    def test_date_range_filter_this_year(self):
        today = date.today()

        this_year_exp = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=date(today.year, 6, 1),
            name="This Year Experiment",
        )
        last_year_exp = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=date(today.year - 1, 6, 1),
            name="Last Year Experiment",
        )

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?date_range={DateRangeChoices.THIS_YEAR}"
        )
        self.assertEqual(response.status_code, 200)

        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(this_year_exp, experiments)
        self.assertNotIn(last_year_exp, experiments)

    def test_date_range_filter_custom_invalid_dates_should_return_all(self):
        exp = NimbusExperimentFactory.create(owner=self.user, name="Test Experiment")

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?date_range={DateRangeChoices.CUSTOM}&start_date=invalid-date"
        )
        self.assertEqual(response.status_code, 200)
        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(exp, experiments)

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?date_range={DateRangeChoices.CUSTOM}&end_date=2024-13-45"
        )
        self.assertEqual(response.status_code, 200)
        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(exp, experiments)

    def test_date_range_filter_no_value_should_return_all(self):
        exp = NimbusExperimentFactory.create(owner=self.user, name="Test Experiment")

        response = self.client.get(f"{reverse('nimbus-ui-home')}?date_range=")
        self.assertEqual(response.status_code, 200)
        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(exp, experiments)

    def test_date_range_filter_custom_no_dates_should_return_all(self):
        exp = NimbusExperimentFactory.create(owner=self.user, name="Test Experiment")

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?date_range={DateRangeChoices.CUSTOM}"
        )
        self.assertEqual(response.status_code, 200)
        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(exp, experiments)

    def test_date_range_filter_with_other_filters_combined(self):
        today = date.today()

        recent_labs = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=today - timedelta(days=5),
            is_firefox_labs_opt_in=True,
            firefox_labs_title="Recent Labs",
            firefox_labs_description="description",
            firefox_labs_group=NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING,
            name="Recent Labs Experiment",
        )
        recent_rollout = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=today - timedelta(days=5),
            is_rollout=True,
            name="Recent Rollout Experiment",
        )
        old_labs = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=today - timedelta(days=15),
            is_firefox_labs_opt_in=True,
            firefox_labs_title="Old Labs",
            firefox_labs_description="description",
            firefox_labs_group=NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING,
            name="Old Labs Experiment",
        )

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?date_range={DateRangeChoices.LAST_7_DAYS}&type=Labs"
        )
        self.assertEqual(response.status_code, 200)

        experiments = response.context["all_my_experiments_page"].object_list
        self.assertIn(recent_labs, experiments)  # Recent AND Labs
        self.assertNotIn(recent_rollout, experiments)  # Recent but NOT Labs
        self.assertNotIn(old_labs, experiments)  # Labs but NOT recent

    def test_date_range_filter_preserves_sort_order(self):
        today = date.today()

        exp_a = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=today - timedelta(days=5),
            name="A Recent Experiment",
        )
        exp_z = NimbusExperimentFactory.create(
            owner=self.user,
            _start_date=today - timedelta(days=3),
            name="Z Recent Experiment",
        )

        response = self.client.get(
            f"{reverse('nimbus-ui-home')}?date_range={DateRangeChoices.LAST_7_DAYS}&sort=name"
        )
        self.assertEqual(response.status_code, 200)

        experiments = list(response.context["all_my_experiments_page"].object_list)
        self.assertIn(exp_a, experiments)
        self.assertIn(exp_z, experiments)

        exp_a_index = experiments.index(exp_a)
        exp_z_index = experiments.index(exp_z)
        self.assertLess(exp_a_index, exp_z_index)

    class TestTagFilter(TestCase):
        def test_filter_by_single_tag(self):
            tag1 = Tag.objects.create(name="Tag1", color="#FF0000")
            tag2 = Tag.objects.create(name="Tag2", color="#00FF00")
            experiment_with_tag1 = NimbusExperimentFactory.create(
                name="Experiment with Tag1"
            )
            experiment_with_tag1.tags.add(tag1)
            experiment_with_tag2 = NimbusExperimentFactory.create(
                name="Experiment with Tag2"
            )
            experiment_with_tag2.tags.add(tag2)
            experiment_with_no_tags = NimbusExperimentFactory.create(
                name="Experiment with No Tags"
            )

            filterset = NimbusExperimentFilter(data={"tags": [tag1.id]})
            filtered_experiments = filterset.qs

            self.assertIn(experiment_with_tag1, filtered_experiments)
            self.assertNotIn(experiment_with_tag2, filtered_experiments)
            self.assertNotIn(experiment_with_no_tags, filtered_experiments)

        def test_filter_by_multiple_tags(self):
            tag1 = Tag.objects.create(name="Tag1", color="#FF0000")
            tag2 = Tag.objects.create(name="Tag2", color="#00FF00")
            experiment_with_tag1 = NimbusExperimentFactory.create(
                name="Experiment with Tag1"
            )
            experiment_with_tag1.tags.add(tag1)
            experiment_with_tag2 = NimbusExperimentFactory.create(
                name="Experiment with Tag2"
            )
            experiment_with_tag2.tags.add(tag2)
            experiment_with_both_tags = NimbusExperimentFactory.create(
                name="Experiment with Both Tags"
            )
            experiment_with_both_tags.tags.add(tag1, tag2)
            experiment_with_no_tags = NimbusExperimentFactory.create(
                name="Experiment with No Tags"
            )

            filterset = NimbusExperimentFilter(data={"tags": [tag1.id, tag2.id]})
            filtered_experiments = filterset.qs

            self.assertIn(experiment_with_both_tags, filtered_experiments)
            self.assertNotIn(experiment_with_tag1, filtered_experiments)
            self.assertNotIn(experiment_with_tag2, filtered_experiments)
            self.assertNotIn(experiment_with_no_tags, filtered_experiments)
