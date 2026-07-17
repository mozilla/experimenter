from django.template import Context
from django.test import RequestFactory, TestCase

from experimenter.base.models import SiteFlag, SiteFlagNameChoices
from experimenter.openidc.tests.factories import UserFactory


class SiteFlagTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._request_factory = RequestFactory()

    def setUp(self):
        super().setUp()

        self.request = self._request_factory.get("/")
        self.request.user = self.user = UserFactory.create(email="dev@example.com")
        self.context = Context(self.get_context_data())

    def get_context_data(self):
        return {
            "request": self.request,
        }

    def _create_advertise_devtools_site_flag(self, value: bool = False, **model_kwargs):
        return SiteFlag.objects.create(
            name=SiteFlagNameChoices.ADVERTISE_DEVTOOLS.name, value=value, **model_kwargs
        )
