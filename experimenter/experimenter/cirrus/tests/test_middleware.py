from unittest import mock

from django.http import QueryDict
from django.test import TestCase
from requests.exceptions import RequestException

from experimenter.cirrus.middleware import CirrusMiddleware


class CirrusMiddlewareTests(TestCase):
    def setUp(self):
        self.response = "Response"

        self.request = mock.Mock()
        self.request.path = "/some/path"
        self.request.user.is_authenticated = True
        self.request.user.id = "test"
        self.request.user.glean_prefs.opt_out = False
        self.request.GET = QueryDict()
        del self.request.cirrus

        self.cirrus_response = {"Features": {}, "Enrollments": []}

    def test_without_user(self):
        del self.request.user

        with self.settings(CIRRUS_URL="cirrus"):
            middleware = CirrusMiddleware(lambda request: self.response)

        with mock.patch(
            "experimenter.cirrus.middleware.requests.post"
        ) as mock_requests_post:
            response = middleware(self.request)

        self.assertEqual(response, self.response)
        self.assertEqual(mock_requests_post.mock_calls, [])
        self.assertIsNone(self.request.cirrus)

    def test_with_glean_opt_out(self):
        self.request.user.glean_prefs.opt_out = True

        with self.settings(CIRRUS_URL="cirrus"):
            middleware = CirrusMiddleware(lambda request: self.response)

        with mock.patch(
            "experimenter.cirrus.middleware.requests.post"
        ) as mock_requests_post:
            response = middleware(self.request)

        self.assertEqual(response, self.response)
        self.assertEqual(mock_requests_post.mock_calls, [])
        self.assertIsNone(self.request.cirrus)

    def test_without_cirrus(self):
        with self.settings(CIRRUS_URL=None):
            middleware = CirrusMiddleware(lambda request: self.response)

        with mock.patch(
            "experimenter.cirrus.middleware.requests.post"
        ) as mock_requests_post:
            response = middleware(self.request)

        self.assertEqual(response, self.response)
        self.assertEqual(mock_requests_post.mock_calls, [])
        self.assertIsNone(self.request.cirrus)

    def test_without_preview_nor_glean_prefs(self):
        del self.request.user.glean_prefs

        with self.settings(CIRRUS_URL="cirrus"):
            middleware = CirrusMiddleware(lambda request: self.response)

        with mock.patch(
            "experimenter.cirrus.middleware.requests.post"
        ) as mock_requests_post:
            mock_requests_post.return_value.json.return_value = self.cirrus_response
            response = middleware(self.request)

        self.assertEqual(response, self.response)
        self.assertIsNotNone(self.request.cirrus)
        self.assertFalse(self.request.cirrus.features.is_example_feature_enabled)
        self.assertIsNone(self.request.cirrus.features.example_feature_emoji)
        self.assertEqual(
            # convert to list for better failure output
            list(mock_requests_post.mock_calls),
            [
                mock.call(
                    "cirrus",
                    json={"client_id": "test", "context": {}},
                    params={},
                ),
                mock.call().raise_for_status(),
                mock.call().json(),
            ],
        )

    def test_with_preview(self):
        self.request.GET = QueryDict("nimbus_preview=true")
        self.cirrus_response["Features"]["example-feature"] = {
            "emoji": "🙂",
            "enabled": True,
        }

        with self.settings(CIRRUS_URL="cirrus"):
            middleware = CirrusMiddleware(lambda request: self.response)

        with mock.patch(
            "experimenter.cirrus.middleware.requests.post"
        ) as mock_requests_post:
            mock_requests_post.return_value.json.return_value = self.cirrus_response
            response = middleware(self.request)

        self.assertEqual(response, self.response)
        self.assertIsNotNone(self.request.cirrus)
        self.assertTrue(self.request.cirrus.features.is_example_feature_enabled)
        self.assertEqual(self.request.cirrus.features.example_feature_emoji, "🙂")
        self.assertEqual(
            # convert to list for better failure output
            list(mock_requests_post.mock_calls),
            [
                mock.call(
                    "cirrus",
                    json={"client_id": "test", "context": {}},
                    params={"nimbus_preview": "true"},
                ),
                mock.call().raise_for_status(),
                mock.call().json(),
            ],
        )

    def test_request_exception(self):
        with self.settings(CIRRUS_URL="cirrus"):
            middleware = CirrusMiddleware(lambda request: self.response)

        with (
            mock.patch(
                "experimenter.cirrus.middleware.requests.post"
            ) as mock_requests_post,
            mock.patch("experimenter.cirrus.middleware.sentry_sdk") as mock_sentry_sdk,
        ):
            mock_requests_post.return_value.raise_for_status.side_effect = (
                RequestException("")
            )
            response = middleware(self.request)

        self.assertEqual(response, self.response)
        self.assertIsNone(self.request.cirrus)
        self.assertEqual(
            list(mock_sentry_sdk.capture_exception.mock_calls),
            [mock.call(mock_requests_post.return_value.raise_for_status.side_effect)],
        )

    def test_key_error(self):
        with self.settings(CIRRUS_URL="cirrus"):
            middleware = CirrusMiddleware(lambda request: self.response)

        with (
            mock.patch(
                "experimenter.cirrus.middleware.requests.post"
            ) as mock_requests_post,
            mock.patch("experimenter.cirrus.middleware.sentry_sdk") as mock_sentry_sdk,
        ):
            mock_requests_post.return_value.json.return_value = {}
            response = middleware(self.request)

        self.assertEqual(response, self.response)
        self.assertIsNone(self.request.cirrus)
        self.assertEqual(
            mock_sentry_sdk.capture_exception.mock_calls,
            [mock.call(mock.ANY)],
        )
        self.assertIsInstance(
            mock_sentry_sdk.capture_exception.call_args.args[0], KeyError
        )
