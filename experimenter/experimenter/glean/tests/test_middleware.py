from unittest import mock

from django.test import TestCase

from experimenter.glean.middleware import GleanMiddleware


class GleanMiddlewareTests(TestCase):
    def setUp(self):
        self.response = "Response"
        # don't record glean metrics in tests
        with self.settings(ENABLE_GLEAN=False):
            self.middleware = GleanMiddleware(lambda request: self.response)

    def test_page_view(self):
        request = mock.Mock()
        request.path = "/some/path"
        request.user.id = 123
        request.user.is_authenticated = True
        del request.user.glean_prefs
        request.cirrus = None

        with (
            mock.patch.object(self.middleware.metrics.url.path, "set") as set_url_path,
            mock.patch.object(
                self.middleware.metrics.nimbus.nimbus_user_id, "set"
            ) as set_user,
            mock.patch.object(
                self.middleware.metrics.nimbus.enrollments, "set"
            ) as set_enrollments,
            mock.patch.object(self.middleware.pings.page_view, "submit") as submit,
        ):
            response = self.middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(set_url_path.mock_calls, [mock.call("/some/path")])
        self.assertEqual(set_user.mock_calls, [mock.call("123")])
        self.assertEqual(set_enrollments.mock_calls, [])
        self.assertEqual(submit.mock_calls, [mock.call()])

    def test_page_view_with_cirrus_enrollments(self):
        request = mock.Mock()
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

        with (
            mock.patch.object(self.middleware.metrics.url.path, "set") as set_url_path,
            mock.patch.object(
                self.middleware.metrics.nimbus.nimbus_user_id, "set"
            ) as set_user,
            mock.patch.object(
                self.middleware.metrics.nimbus.enrollments, "set"
            ) as set_enrollments,
            mock.patch.object(self.middleware.pings.page_view, "submit") as submit,
        ):
            response = self.middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(set_url_path.mock_calls, [mock.call("/some/path")])
        self.assertEqual(set_user.mock_calls, [mock.call("123")])
        self.assertEqual(
            list(set_enrollments.mock_calls),
            [
                mock.call(
                    [
                        {
                            "app_id": "experimenter_cirrus",
                            "branch": "some-branch",
                            "experiment": "some-experiment",
                            "experiment_type": "rollout",
                            "is_preview": False,
                            "nimbus_user_id": "not-123",
                        }
                    ]
                )
            ],
        )
        self.assertEqual(submit.mock_calls, [mock.call()])
