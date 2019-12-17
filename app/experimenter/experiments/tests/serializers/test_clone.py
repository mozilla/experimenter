
from django.test import TestCase

from experimenter.experiments.tests.factories import ExperimentFactory


from experimenter.experiments.serializers.clone import ExperimentCloneSerializer
from experimenter.experiments.tests.mixins import MockRequestMixin


class TestCloneSerializer(MockRequestMixin, TestCase):

    def test_clone_serializer_rejects_duplicate_slug(self):
        experiment_1 = ExperimentFactory.create(
            name="good experiment", slug="great-experiment"
        )
        clone_data = {"name": "great experiment"}
        serializer = ExperimentCloneSerializer(instance=experiment_1, data=clone_data)

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_rejects_duplicate_name(self):
        experiment = ExperimentFactory.create(
            name="wonderful experiment", slug="amazing-experiment"
        )
        clone_data = {"name": "wonderful experiment"}
        serializer = ExperimentCloneSerializer(instance=experiment, data=clone_data)

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_rejects_invalid_name(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )

        clone_data = {"name": "@@@@@@@@"}
        serializer = ExperimentCloneSerializer(instance=experiment, data=clone_data)

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_accepts_unique_name(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        clone_data = {"name": "best experiment"}
        serializer = ExperimentCloneSerializer(
            instance=experiment, data=clone_data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())

        serializer.save()

        self.assertEqual(serializer.data["name"], "best experiment")
        self.assertEqual(serializer.data["clone_url"], "/experiments/best-experiment/")
