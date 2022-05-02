from django.test import TestCase

from experimenter.base.serializers import (
    CountrySerializer,
    LocaleSerializer,
    LanguageSerializer,
)
from experimenter.base.tests.factories import (
    CountryFactory,
    LocaleFactory,
    LanguageFactory,
)


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


class TestLanguageSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        language = LanguageFactory.create()
        serializer = LanguageSerializer(language)
        self.assertEqual(serializer.data, {"code": language.code, "name": language.name})
