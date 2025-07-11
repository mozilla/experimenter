from unittest import mock

from django.test import TestCase

from experimenter.glean.middleware import GleanMiddleware


class GleanMiddlewareTests(TestCase):
    def setUp(self):
        self.response = "Response"
        # don't record glean metrics in tests
        with self.settings(ENABLE_GLEAN=False):
            self.middleware = GleanMiddleware(lambda request: self.response)

    def test_page_view_recorded(self):
        request = mock.Mock()
        request.path = "/some/path"
        request.user = mock.Mock()
        request.user.id = "test"
        with mock.patch(self.middleware.metrics.page.view, "record") as record:
            response = self.middleware(request)
        self.assertEqual(record.call_count, 1)
        self.assertEqual(
            record.call_args,
            [
                call(
                    self.middleware.metrics.page.ViewExtra(
                        path="/some/path", nimbus_user_id="test"
                    )
                )
            ],
        )
        self.assertEqual(response, self.response)
