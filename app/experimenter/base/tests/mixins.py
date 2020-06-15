import mock

from experimenter.openidc.tests.factories import UserFactory


class MockRequestMixin(object):
    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.request = mock.Mock()
        self.request.user = self.user
