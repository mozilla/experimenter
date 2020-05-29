from django.test import TestCase

from experimenter.base.serializers import CountrySerializer, LocaleSerializer
from experimenter.base.tests.factories import CountryFactory, LocaleFactory


class TestLocaleSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        locale = LocaleFactory.create()
        serializer = LocaleSerializer(locale)
        self.assertEqual(serializer.data, {"code": locale.code, "name": locale.name})


class TestCountrySerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        country = CountryFactory.create()
        serializer = CountrySerializer(country)
        self.assertEqual(serializer.data, {"code": country.code, "name": country.name})
