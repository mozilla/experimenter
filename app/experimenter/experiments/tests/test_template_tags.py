from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase


class TestPaginationUrl(SimpleTestCase):
    def test_it_works(self):
        context = Context({"request": RequestFactory().get("/")})
        template_to_render = Template(
            "{% load experiment_extras %}" "{% pagination_url 123 %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertEqual("?page=123", rendered_template)

    def test_with_other_keys(self):
        context = Context({"request": RequestFactory().get("/", {"foo": "bar"})})
        template_to_render = Template(
            "{% load experiment_extras %}" "{% pagination_url 2 %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertEqual("?foo=bar&amp;page=2", rendered_template)

    def test_next_page(self):
        context = Context({"request": RequestFactory().get("/", {"page": 1})})
        template_to_render = Template(
            "{% load experiment_extras %}" "{% pagination_url 2 %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertEqual("?page=2", rendered_template)

    def test_back_to_first_page(self):
        context = Context({"request": RequestFactory().get("/", {"page": 2})})
        template_to_render = Template(
            "{% load experiment_extras %}" "{% pagination_url 1 %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertEqual(".", rendered_template)

    def test_back_to_first_page_with_other_data(self):
        context = Context({"request": RequestFactory().get("/", {"foo": "bar"})})
        template_to_render = Template(
            "{% load experiment_extras %}" "{% pagination_url 1 %}"
        )
        rendered_template = template_to_render.render(context)
        self.assertEqual("?foo=bar", rendered_template)


class TestAsJson(SimpleTestCase):
    def test_formats_json(self):
        context = Context({"json_val": '{"key": "value"}'})
        template = Template(
            """
            {% load experiment_extras %}
            {{ json_val|as_json }}
          """
        )
        rendered = template.render(context)
        self.assertEqual(
            rendered.strip().replace(" ", "").replace("\n", ""),
            "{&quot;key&quot;:&quot;value&quot;}",
        )
