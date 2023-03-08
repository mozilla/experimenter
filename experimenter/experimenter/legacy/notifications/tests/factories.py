import factory
from faker import Factory as FakerFactory

from experimenter.legacy.notifications.models import Notification
from experimenter.openidc.tests.factories import UserFactory

faker = FakerFactory.create()


class NotificationFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    message = faker.catch_phrase()

    class Meta:
        model = Notification
