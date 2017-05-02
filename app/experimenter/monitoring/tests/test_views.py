import json

import mock
from django.core.urlresolvers import reverse
from django.db import OperationalError
from django.test import TestCase


class VersionViewTests(TestCase):

    def test_version_endpoint_returns_version_info_json(self):
        version_info = {
            'source': 'http://path/to/repo',
            'version': '1.0',
            'commit': 'abcdefg',
        }

        with self.settings(GIT_VERSION_INFO=version_info):
            response = self.client.get(reverse('monitoring-version'))

            self.assertEquals(response.status_code, 200)
            self.assertEquals(json.loads(response.content), version_info)


class HearbeatViewTests(TestCase):

    def test_heartbeat_view_returns_200_if_able_to_reach_db(self):
        response = self.client.get(reverse('monitoring-heartbeat'))
        self.assertEqual(response.status_code, 200)

    @mock.patch('experimenter.monitoring.views.connections')
    def test_heartbeat_view_fails_if_unable_to_reach_db(self, mocked_conn):
        mocked_conn['default'].cursor.side_effect = OperationalError

        response = self.client.get(reverse('monitoring-heartbeat'))
        self.assertEqual(response.status_code, 400)


class LBHearbeatViewTests(TestCase):

    def test_heartbeat_view_returns_200(self):
        response = self.client.get(reverse('monitoring-lbheartbeat'))
        self.assertEqual(response.status_code, 200)
