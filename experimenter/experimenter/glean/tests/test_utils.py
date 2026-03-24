from unittest import mock

from django.test import TestCase

from experimenter.glean.utils import get_request_ip


class GleancUtilsTest(TestCase):
    def test_get_request_ip(self):
        request = mock.Mock()
        # check fallback to REMOTE_ADDR
        request.META = {"REMOTE_ADDR": "127.0.0.1"}
        self.assertEqual(get_request_ip(request), "127.0.0.1")
        # check XFF
        request.META["HTTP_X_FORWARDED_FOR"] = "::4,::3,::2,::1"
        self.assertEqual(get_request_ip(request), "::3")
        request.META["HTTP_X_FORWARDED_FOR"] = "::3,::2,::1"
        self.assertEqual(get_request_ip(request), "::3")
        request.META["HTTP_X_FORWARDED_FOR"] = "::2,::1"
        self.assertEqual(get_request_ip(request), "::2")
        request.META["HTTP_X_FORWARDED_FOR"] = "::1"
        self.assertEqual(get_request_ip(request), "::1")
