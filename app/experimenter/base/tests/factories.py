import factory
from faker import Factory as FakerFactory

from experimenter.base.models import Country, Locale

faker = FakerFactory.create()


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
