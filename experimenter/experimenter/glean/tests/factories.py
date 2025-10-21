import factory

from experimenter.glean.models import Prefs
from experimenter.openidc.tests.factories import UserFactory


class PrefsFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    alert_dismissed = False
    opt_out = False

    class Meta:
        model = Prefs
        django_get_or_create = ("alert_dismissed", "opt_out")
