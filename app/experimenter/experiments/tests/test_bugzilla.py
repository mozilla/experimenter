import json

import mock
from requests.exceptions import RequestException
from django.test import TestCase
from django.conf import settings

from experimenter.experiments.models import Experiment
from experimenter.experiments.bugzilla import create_experiment_bug
from experimenter.experiments.tests.factories import ExperimentFactory


class MockBugzillaMixin(object):

    def setUp(self):
        super().setUp()

        mock_bugzilla_requests_post_patcher = mock.patch(
            "experimenter.experiments.bugzilla.requests.post"
        )
        self.mock_bugzilla_requests_post = (
            mock_bugzilla_requests_post_patcher.start()
        )
        self.addCleanup(mock_bugzilla_requests_post_patcher.stop)

        self.bugzilla_id = "12345"
        mock_response_data = {"id": self.bugzilla_id}
        mock_response = mock.Mock()
        mock_response.content = json.dumps(mock_response_data)
        self.mock_bugzilla_requests_post.return_value = mock_response


class TestBugzilla(MockBugzillaMixin, TestCase):

    def test_creating_bugzilla_ticket_returns_ticket_id(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        create_experiment_bug(experiment)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_CREATE_URL,
            {
                "product": "Shield",
                "component": "Shield Study",
                "version": "unspecified",
                "summary": "[Shield] Pref Flip Study: An Experiment",
                "description": experiment.BUGZILLA_TEMPLATE.format(
                    experiment=experiment
                ),
                "assigned_to": experiment.owner.email,
                "cc": settings.BUGZILLA_CC_LIST,
            },
        )

    def test_request_error_passes_silently(self):
        self.mock_bugzilla_requests_post.side_effect = RequestException()

        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        bugzilla_id = create_experiment_bug(experiment)
        self.assertEqual(bugzilla_id, None)

    def test_json_parse_error_passes_silently(self):
        mock_response = mock.Mock()
        mock_response.content = "{invalid json"
        self.mock_bugzilla_requests_post.return_value = mock_response

        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        bugzilla_id = create_experiment_bug(experiment)
        self.assertEqual(bugzilla_id, None)
