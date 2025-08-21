import datetime

from django.test import TestCase
from django.urls import reverse
from parameterized import parameterized

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    UserFactory,
    generate_nimbus_changelog,
)
from experimenter.nimbus_ui.filtersets import (
    HomeSortChoices,
    MyDeliveriesChoices,
)
from experimenter.nimbus_ui.templatetags.nimbus_extras import (
    format_json,
    format_not_set,
    remove_underscores,
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


class TestHomeFilters(AuthTestCase):
    def _make_three_types(self):
        labs = NimbusExperimentFactory.create(
            owner=self.user,
            is_firefox_labs_opt_in=True,
            is_rollout=False,
            name="Labs One",
        )
        rollout = NimbusExperimentFactory.create(
            owner=self.user,
            is_firefox_labs_opt_in=False,
            is_rollout=True,
            name="Rollout One",
        )
        experiment = NimbusExperimentFactory.create(
            owner=self.user,
            is_firefox_labs_opt_in=False,
            is_rollout=False,
            name="Experiment One",
        )
        return labs, rollout, experiment

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
            population_percent=5,
            firefox_min_version=120,
        )
        high = NimbusExperimentFactory.create(
            owner=self.user,
            name="Z High",
            application=NimbusExperiment.Application.DESKTOP,
            is_rollout=True,
            channel=NimbusExperiment.Channel.RELEASE,
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

    def test_filter_type_labs_only(self):
        labs, rollout, experiment = self._make_three_types()

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?type=Labs")
        self.assertEqual(resp.status_code, 200)

        page = list(resp.context["all_my_experiments_page"].object_list)
        self.assertIn(labs, page)
        self.assertNotIn(rollout, page)
        self.assertNotIn(experiment, page)

    def test_filter_type_rollout_only(self):
        labs, rollout, experiment = self._make_three_types()

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?type=Rollout")
        self.assertEqual(resp.status_code, 200)

        page = list(resp.context["all_my_experiments_page"].object_list)
        self.assertIn(rollout, page)
        self.assertNotIn(labs, page)
        self.assertNotIn(experiment, page)

    def test_filter_type_experiment_only(self):
        labs, rollout, experiment = self._make_three_types()

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?type=Experiment")
        self.assertEqual(resp.status_code, 200)

        page = list(resp.context["all_my_experiments_page"].object_list)
        self.assertIn(experiment, page)
        self.assertNotIn(labs, page)
        self.assertNotIn(rollout, page)

    def test_filter_type_multi_select_labs_and_rollout(self):
        labs, rollout, experiment = self._make_three_types()

        url = f"{reverse('nimbus-ui-home')}?type=Labs&type=Rollout"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        page = list(resp.context["all_my_experiments_page"].object_list)
        self.assertIn(labs, page)
        self.assertIn(rollout, page)
        self.assertNotIn(experiment, page)

    def test_filter_type_with_sort_preserved(self):
        labs, rollout, experiment = self._make_three_types()

        resp = self.client.get(f"{reverse('nimbus-ui-home')}?type=Labs&sort=name")
        self.assertEqual(resp.status_code, 200)

        page = list(resp.context["all_my_experiments_page"].object_list)
        self.assertEqual(page, [labs])
