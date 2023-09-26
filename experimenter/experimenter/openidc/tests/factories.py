import factory
from django.contrib.auth.models import User
from faker import Faker

faker = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    first_name = factory.LazyAttribute(lambda o: faker.first_name())
    last_name = factory.LazyAttribute(lambda o: faker.last_name())
    email = factory.LazyAttribute(lambda o: faker.company_email())
    username = factory.LazyAttribute(lambda o: o.email)

    class Meta:
        model = User
