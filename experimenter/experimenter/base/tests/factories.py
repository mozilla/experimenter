import factory
from faker import Faker

from experimenter.base.models import Country, Language, Locale

faker = Faker()


class CountryFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda o: faker.country())
    code = factory.LazyAttribute(lambda o: o.name[:2])

    class Meta:
        model = Country
        django_get_or_create = ("code",)


class LocaleFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda o: faker.locale())
    code = factory.LazyAttribute(lambda o: o.name[:2])

    class Meta:
        model = Locale
        django_get_or_create = ("code",)


class LanguageFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    code = factory.LazyAttribute(lambda o: o.name[:2])

    class Meta:
        model = Language
        django_get_or_create = ("code",)
