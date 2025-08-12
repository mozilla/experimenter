from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
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

    def test_all_home_sort_choices_do_not_error(self):
        for i, sort_choice in enumerate(HomeSortChoices):
            with self.subTest(sort=sort_choice.value):
                NimbusExperimentFactory.create(
                    owner=self.user,
                    name=f"Sort Test {i}",
                )
                response = self.client.get(
                    f"{reverse('nimbus-ui-home')}?sort={sort_choice.value}"
                )
                self.assertEqual(response.status_code, 200)
