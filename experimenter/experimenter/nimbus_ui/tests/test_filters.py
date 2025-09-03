import datetime

from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
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
    HomeSortChoices,
    MyDeliveriesChoices,
)
from experimenter.nimbus_ui.templatetags.nimbus_extras import (
    application_icon_info,
    channel_icon_info,
    choices_with_icons,
    format_json,
    format_not_set,
    home_status_display,
    qa_icon_info,
    remove_underscores,
    render_channel_icons,
    status_icon_info,
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
            (HomeSortChoices.VERSIONS_UP, HomeSortChoices.VERSIONS_DOWN),
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
