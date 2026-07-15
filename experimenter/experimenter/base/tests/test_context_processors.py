from textwrap import dedent

from django.template import Template

from experimenter.base.context_processors import site_flag_enabled
from experimenter.base.tests import SiteFlagTestCase


class SiteFlagTemplateTagTests(SiteFlagTestCase):
    ADVERTISE_DEVTOOLS_TEMPLATE = Template(
        dedent("""\
        {% if site_flag_enabled.ADVERTISE_DEVTOOLS %}
            true
        {% else %}
            false
        {% endif %}
    """)
    )

    def get_context_data(self):
        return {**super().get_context_data(), **site_flag_enabled(self.request)}

    def test_site_flag_cached(self):
        self._create_advertise_devtools_site_flag()

        with self.assertNumQueries(1):
            self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)

        with self.assertNumQueries(0):
            self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)

    def test_site_flag_enabled_not_exists(self):
        content = self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)
        self.assertEqual(content.strip(), "false")

    def test_site_flag_enabled_false(self):
        self._create_advertise_devtools_site_flag()

        content = self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)
        self.assertEqual(content.strip(), "false")

    def test_site_flag_enabled_true(self):
        self._create_advertise_devtools_site_flag(value=True)

        content = self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)
        self.assertEqual(content.strip(), "true")
