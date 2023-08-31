from django.test import TestCase

from experimenter.base.serializers import (
    CountrySerializer,
    LanguageSerializer,
    LocaleSerializer,
)
from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
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
        self.assertEqual(
            str(language), f"{serializer.data['name']} ({serializer.data['code']})"
        )
        self.assertEqual(serializer.data, {"code": language.code, "name": language.name})
