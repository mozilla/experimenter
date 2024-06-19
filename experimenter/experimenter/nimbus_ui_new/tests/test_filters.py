from django.test import TestCase

from experimenter.nimbus_ui_new.templatetags.nimbus_extras import (
    format_not_set,
    format_to_title,
    yesno,
)


class FilterTests(TestCase):
    def test_yesno_filter(self):
        """Test the yesno filter handles truthy, falsy, and None values."""
        self.assertEqual(yesno(True), "Yes")
        self.assertEqual(yesno(False), "No")
        self.assertEqual(yesno(None), "")

    def test_format_to_title(self):
        self.assertEqual(format_to_title("test_example"), "Test Example")
        self.assertEqual(
            format_to_title("another_test_example"),
            "Another Test Example",
        )

    def test_format_not_set(self):
        self.assertEqual(
            format_not_set(""),
            '<span style="color: red;">Not set</span>',
        )
        self.assertEqual(
            format_not_set(None),
            '<span style="color: red;">Not set</span>',
        )
        self.assertEqual(format_not_set("Some value"), "Some value")
