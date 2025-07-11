from unittest import mock

from django.test import TestCase
from pytest_httpserver import HTTPServer
from pytest.mark import parametrize

from experimenter.cirrus.middleware import CirrusMiddleware


class CirrusMiddlewareTests(TestCase):
    def setUp(self):
        self.response = "Response"

    @parametrize("has_user", [False, True])
    @parametrize("has_cirrus", [False, True])
    def test_cirrus_requires_user_and_url(self, has_user, has_cirrus):
        request = mock.Mock()
        request.path = "/some/path"

        if has_user:
            request.user.id = "test"
        else:
            del request.user

        cirrus_response = {"Features": {}, "Enrollments": []}
        if has_cirrus:
            httpserver.expect_request("/v2/features/").respond_with_json(cirrus_response)
            CIRRUS_URL = httpserver.url_for("/v2/features/")
        else:
            CIRRUS_URL = ""

        with self.settings(CIRRUS_URL=CIRRUS_URL):
            middleware = CirrusMiddleware(lambda request: self.response)
        response = middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(
            request.cirrus, cirrus_response if has_user and has_cirrus else {}
        )
