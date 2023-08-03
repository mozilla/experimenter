from django.test import TestCase
from experimenter.experiments.constants import NimbusConstants

class ChangeEventEnumTestCase(TestCase):

    def test_enum_values(self):
        self.assertEqual(NimbusConstants.ChangeEvent.STATUS.value, "STATUS_CHANGE")
        self.assertEqual(NimbusConstants.ChangeEvent.PUBLISH_STATUS.value, "PUBLISH_STATUS_CHANGE")
        self.assertEqual(NimbusConstants.ChangeEvent.IS_PAUSED.value, "BOOLEAN")
        self.assertEqual(NimbusConstants.ChangeEvent.IS_ARCHIVED.value, "BOOLEAN")
        self.assertEqual(NimbusConstants.ChangeEvent.POPULATION_PERCENTAGE.value, "LIVE_CHANGE")

    def test_display_name(self):
        self.assertEqual(NimbusConstants.ChangeEvent.STATUS.display_name, "Status")
        self.assertEqual(NimbusConstants.ChangeEvent.PUBLISH_STATUS.display_name, "Publish Status")
        self.assertEqual(NimbusConstants.ChangeEvent.IS_PAUSED.display_name, "Pause Enrollment Flag")
        self.assertEqual(NimbusConstants.ChangeEvent.IS_ARCHIVED.display_name, "Archive Experiment Flag")
        self.assertEqual(NimbusConstants.ChangeEvent.POPULATION_PERCENTAGE.display_name, "Population Percentage")

    def test_find_enum_by_key(self):
        self.assertEqual(NimbusConstants.ChangeEvent.find_enum_by_key("STATUS"), NimbusConstants.ChangeEvent.STATUS)
        self.assertEqual(NimbusConstants.ChangeEvent.find_enum_by_key("INVALID_KEY"), NimbusConstants.ChangeEvent.GENERAL)

