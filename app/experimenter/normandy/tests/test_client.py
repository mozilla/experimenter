import mock
from django.conf import settings
from django.test import TestCase
from requests.exceptions import HTTPError, RequestException

from experimenter.normandy import (
    APINormandyError,
    NonsuccessfulNormandyCall,
    NormandyDecodeError,
    get_recipe,
    make_normandy_call,
)
from experimenter.normandy.client import get_history_list
from experimenter.normandy.tests.mixins import MockNormandyMixin


class TestMakeNormandyCall(MockNormandyMixin, TestCase):
    def test_sucessful_call(self):
        mock_response_data = {"detail": "Not found."}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        self.mock_normandy_requests_get.return_value = mock_response

        response_data = make_normandy_call("/url/")

        self.assertEqual(response_data, mock_response_data)

    def test_make_normandy_call_with_request_exception(self):
        self.mock_normandy_requests_get.side_effect = RequestException()

        with self.assertRaises(APINormandyError) as e:
            make_normandy_call("/url/")
            self.assertEqual(
                e.message, "Normandy API returned Nonsuccessful Response Code"
            )

    def test_make_normandy_call_with_HTTP_error(self):
        self.mock_normandy_requests_get.side_effect = HTTPError()
        with self.assertRaises(NonsuccessfulNormandyCall) as e:
            make_normandy_call("/url/")
            self.assertEqual(e.message, "Error calling Normandy API")

    def test_make_normandy_call_with_value_error(self):
        self.mock_normandy_requests_get.side_effect = ValueError()
        with self.assertRaises(NormandyDecodeError) as e:
            make_normandy_call("/url/")
            self.assertEqual(e.message, "Error parsing JSON Normandy Response")

    def test_successful_get_recipe_returns_recipe_data(self):
        response_data = get_recipe(1234)
        self.assertTrue(response_data["enabled"])

    def test_successful_get_history_list_returns_response(self):
        mock_response_data = {"detail": "Not found."}
        mock_response = mock.Mock()
        mock_response.json.return_value = mock_response_data
        self.mock_normandy_requests_get.return_value = mock_response

        with self.settings(APP_VERSION=None):
            test_id = 1234
            url = settings.NORMANDY_API_HISTORY_URL.format(id=test_id)

        response_data = get_history_list(url)
        self.assertEqual(response_data, mock_response_data)
