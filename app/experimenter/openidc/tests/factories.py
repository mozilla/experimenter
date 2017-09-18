import factory
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from faker import Factory as FakerFactory

faker = FakerFactory.create()


class UserFactory(factory.django.DjangoModelFactory):
    first_name = factory.LazyAttribute(lambda o: faker.first_name())
    last_name = factory.LazyAttribute(lambda o: faker.last_name())
    username = factory.LazyAttribute(
        lambda o: '{}-{}'.format(slugify(o.first_name), slugify(o.last_name)))
    email = factory.LazyAttribute(
        lambda o: '{}@example.com'.format(o.username))

    class Meta:
        model = get_user_model()
