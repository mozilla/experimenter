import json
import re
from textwrap import dedent

from django.template import Template

from experimenter.base.tests import SiteFlagTestCase


class SiteFlagTemplateTagTests(SiteFlagTestCase):
    ADVERTISE_DEVTOOLS_TEMPLATE = Template(
        dedent("""\
        {% load site_flags %}
        {% site_flag_extra_data "ADVERTISE_DEVTOOLS" "advertise-nimbus-devtools-json" %}
    """)
    )

    def test_site_flag_cached(self):
        self._create_advertise_devtools_site_flag()

        with self.assertNumQueries(1):
            self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)

        with self.assertNumQueries(0):
            self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)

    def test_site_flag_extra_data_not_exists(self):
        content = self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)
        self.assertEqual(content.strip(), "")

    def test_site_flag_extra_data_empty(self):
        self._create_advertise_devtools_site_flag()

        content = self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)
        self.assertEqual(content.strip(), "")

    def test_site_flag_extra_data(self):
        self._create_advertise_devtools_site_flag(
            extra_data={
                "availableDevtoolsVersion": [0, 1, 2],
            }
        )

        content = self.ADVERTISE_DEVTOOLS_TEMPLATE.render(self.context)

        match = re.match(r"^<script[^>]+>([^<]*)</script>$", content.strip())
        self.assertIsNotNone(match)

        value = json.loads(match[1])
        self.assertEqual(value, {"availableDevtoolsVersion": [0, 1, 2]})
