from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import Resolver404

from experimenter.openidc.middleware import OpenIDCAuthMiddleware


class OpenIDCAuthMiddlewareTests(TestCase):
    def setUp(self):
        self.response = "Response"
        self.middleware = OpenIDCAuthMiddleware(lambda request: self.response)

        mock_resolve_patcher = mock.patch("experimenter.openidc.middleware.resolve")
        self.mock_resolve = mock_resolve_patcher.start()
        self.addCleanup(mock_resolve_patcher.stop)

    def test_whitelisted_url_is_not_authed(self):
        request = mock.Mock()
        request.path = "/whitelisted-view/"
        whitelisted_view_name = "whitelisted-view"

        with self.settings(OPENIDC_AUTH_WHITELIST=[whitelisted_view_name]):
            mock_view = mock.Mock()
            mock_view.url_name = whitelisted_view_name
            self.mock_resolve.return_value = mock_view

            response = self.middleware(request)
            self.assertEqual(response, self.response)

    def test_404_path_forces_authentication(self):
        request = mock.Mock()
        request.META = {}

        self.mock_resolve.side_effect = Resolver404

        if response := self.middleware(request):
            self.assertEqual(response.status_code, 401)

    def test_request_missing_headers_raises_401(self):
        request = mock.Mock()
        request.META = {}

        with self.settings(OPENIDC_AUTH_WHITELIST=[]):
            response = self.middleware(request)

        if response:
            self.assertEqual(response.status_code, 401)

    def test_user_created_with_correct_email_from_header(self):
        user_email = "user@example.com"

        request = mock.Mock()
        request.META = {settings.OPENIDC_EMAIL_HEADER: user_email}

        self.assertEqual(User.objects.all().count(), 0)

        with self.settings(OPENIDC_AUTH_WHITELIST=[]):
            response = self.middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(User.objects.all().count(), 1)

        self.assertEqual(request.user.email, user_email)
        self.assertFalse(request.user.is_staff)

    def test_dev_user_is_super_staff_user_when_debug_true(self):
        dev_email = "dev@example.com"

        request = mock.Mock()
        request.META = {settings.OPENIDC_EMAIL_HEADER: dev_email}

        self.assertEqual(User.objects.all().count(), 0)

        with self.settings(
            OPENIDC_AUTH_WHITELIST=[], DEBUG=True, DEV_USER_EMAIL="dev@example.com"
        ):
            response = self.middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(User.objects.all().count(), 1)

        self.assertEqual(request.user.email, dev_email)
        self.assertTrue(request.user.is_staff)
        self.assertTrue(request.user.is_superuser)

    def test_dev_user_is_not_super_staff_user_when_debug_false(self):
        dev_email = "dev@example.com"

        request = mock.Mock()
        request.META = {settings.OPENIDC_EMAIL_HEADER: dev_email}

        self.assertEqual(User.objects.all().count(), 0)

        with self.settings(
            OPENIDC_AUTH_WHITELIST=[], DEBUG=False, DEV_USER_EMAIL="dev@example.com"
        ):
            response = self.middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(User.objects.all().count(), 1)

        self.assertEqual(request.user.email, dev_email)
        self.assertFalse(request.user.is_staff)
        self.assertFalse(request.user.is_superuser)

    def test_dev_user_email_used_when_debug_true_and_no_openidc_header_passed(self):
        dev_email = "dev@example.com"
        request = mock.Mock()
        request.META = {}

        with self.settings(
            OPENIDC_AUTH_WHITELIST=[], DEBUG=True, DEV_USER_EMAIL=dev_email
        ):
            response = self.middleware(request)

        self.assertEqual(response, self.response)
        self.assertEqual(User.objects.all().count(), 1)

        self.assertEqual(request.user.email, dev_email)
        self.assertTrue(request.user.is_staff)
        self.assertTrue(request.user.is_superuser)

    def test_dev_user_email_not_used_when_debug_false_and_no_openidc_header_passed(self):
        dev_email = "dev@example.com"
        request = mock.Mock()
        request.META = {}

        with self.settings(
            OPENIDC_AUTH_WHITELIST=[], DEBUG=False, DEV_USER_EMAIL=dev_email
        ):
            response = self.middleware(request)

        if response:
            self.assertEqual(response.content, b"Please login using OpenID Connect")
            self.assertEqual(User.objects.all().count(), 0)
