from unittest import mock

from django.test import TestCase

from experimenter.glean.middleware import GleanMiddleware


class GleanMiddlewareTests(TestCase):
    def setUp(self):
        self.response = "Response"
        self.middleware = GleanMiddleware(lambda request: self.response)

    def test_page_view(self):
        request = mock.Mock()
        request.META.get.return_value = None
        request.path = "/some/path"
        request.user.id = 123
        request.user.is_authenticated = True
        del request.user.glean_prefs
        request.cirrus = None

        with mock.patch.object(self.middleware.page_view_ping, "record") as record:
            response = self.middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(
            record.mock_calls,
            [
                mock.call(
                    user_agent=None,
                    ip_address=None,
                    nimbus_enrollments=None,
                    nimbus_nimbus_user_id="123",
                    url_path="/some/path",
                    events=[],
                )
            ],
        )

    def test_page_view_with_cirrus_enrollments(self):
        request = mock.Mock()
        request.META.get.return_value = None
        request.path = "/some/path"
        request.user.id = 123
        request.user.is_authenticated = True
        request.user.glean_prefs.opt_out = False
        request.cirrus.enrollments = [
            {
                "app_id": "experimenter_cirrus",
                "branch": "some-branch",
                "experiment": "some-experiment",
                "experiment_type": "rollout",
                "is_preview": "false",
                "nimbus_user_id": "not-123",
            }
        ]

        with mock.patch.object(self.middleware.page_view_ping, "record") as record:
            response = self.middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(
            record.mock_calls,
            [
                mock.call(
                    user_agent=None,
                    ip_address=None,
                    nimbus_enrollments=[
                        {
                            "app_id": "experimenter_cirrus",
                            "branch": "some-branch",
                            "experiment": "some-experiment",
                            "experiment_type": "rollout",
                            "is_preview": False,
                            "nimbus_user_id": "not-123",
                        }
                    ],
                    nimbus_nimbus_user_id="123",
                    url_path="/some/path",
                    events=[],
                )
            ],
        )
