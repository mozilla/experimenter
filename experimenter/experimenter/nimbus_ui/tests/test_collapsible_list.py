from django.template.loader import render_to_string
from django.test import TestCase


class CollapsibleListTemplateTest(TestCase):
    template = "common/collapsible_list.html"

    def test_empty_items_renders_empty_text(self):
        rendered = render_to_string(
            self.template, {"items": [], "empty_text": "All Locales", "id": "x"}
        )
        self.assertIn("All Locales", rendered)
        self.assertNotIn("collapse", rendered)
        self.assertNotIn("Show", rendered)

    def test_short_list_renders_inline_without_toggle(self):
        items = [f"item-{i}" for i in range(10)]
        rendered = render_to_string(
            self.template, {"items": items, "empty_text": "All", "id": "x"}
        )
        for item in items:
            self.assertIn(item, rendered)
        self.assertNotIn("All", rendered)
        self.assertNotIn('data-bs-toggle="collapse"', rendered)
        self.assertNotIn("Show less", rendered)

    def test_long_list_renders_collapsible_with_toggle(self):
        items = [f"item-{i}" for i in range(15)]
        rendered = render_to_string(
            self.template, {"items": items, "empty_text": "All", "id": "my-list"}
        )
        for item in items:
            self.assertIn(item, rendered)
        self.assertIn('data-bs-toggle="collapse"', rendered)
        self.assertIn('data-bs-target="#my-list"', rendered)
        self.assertIn('id="my-list"', rendered)
        self.assertIn("Show 5 more", rendered)
        self.assertIn("Show less", rendered)
        self.assertIn('class="collapse"', rendered)

    def test_exactly_eleven_items_collapses_with_one_hidden(self):
        items = [f"item-{i}" for i in range(11)]
        rendered = render_to_string(
            self.template, {"items": items, "empty_text": "All", "id": "y"}
        )
        self.assertIn("Show 1 more", rendered)
