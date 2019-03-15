import factory

from experimenter.base.models import Country, Locale


class LocaleFactory(factory.django.DjangoModelFactory):
    code = "en-US"
    name = "English (US)"

    class Meta:
        model = Locale
        django_get_or_create = ("code",)


class CountryFactory(factory.django.DjangoModelFactory):
    code = "US"
    name = "United States of America"

    class Meta:
        model = Country
        django_get_or_create = ("code",)
