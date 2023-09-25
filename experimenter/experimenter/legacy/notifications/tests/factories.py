import factory
from faker import Faker

from experimenter.legacy.notifications.models import Notification
from experimenter.openidc.tests.factories import UserFactory

faker = Faker()


class NotificationFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    message = faker.unique.catch_phrase()

    class Meta:
        model = Notification
