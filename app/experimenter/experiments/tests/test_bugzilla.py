import json

import mock
from requests.exceptions import RequestException
from django.test import TestCase
from django.conf import settings

from experimenter.experiments.models import Experiment
from experimenter.experiments.bugzilla import (
    add_experiment_comment,
    create_experiment_bug,
    format_bug_body,
    make_bugzilla_call,
)
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
        mock_response.status_code = 200
        self.mock_bugzilla_requests_post.return_value = mock_response


class TestBugzilla(MockBugzillaMixin, TestCase):

    def test_creating_pref_bugzilla_ticket_returns_ticket_id(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        bugzilla_id = create_experiment_bug(experiment)

        self.assertEqual(bugzilla_id, self.bugzilla_id)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_CREATE_URL,
            {
                "product": "Shield",
                "component": "Shield Study",
                "version": "unspecified",
                "summary": "[Shield] {experiment}".format(
                    experiment=experiment
                ),
                "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
                    experiment=experiment
                ),
                "assigned_to": experiment.owner.email,
                "cc": settings.BUGZILLA_CC_LIST,
            },
        )

    def test_add_bugzilla_comment_pref_study(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_PREF,
        )

        comment_id = add_experiment_comment(experiment)

        self.assertEqual(comment_id, self.bugzilla_id)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
            {"comment": format_bug_body(experiment)},
        )

    def test_add_bugzilla_comment_addon_study(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_ADDON,
        )

        comment_id = add_experiment_comment(experiment)

        self.assertEqual(comment_id, self.bugzilla_id)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
            {"comment": format_bug_body(experiment)},
        )

    @mock.patch("experimenter.experiments.bugzilla.logging")
    def test_api_error_logs_message(self, mock_logging):
        mock_response_data = {
            "message": "Error creating Bugzilla Bug because of reasons"
        }
        mock_response = mock.Mock()
        mock_response.content = json.dumps(mock_response_data)
        mock_response.status_code = 400
        self.mock_bugzilla_requests_post.return_value = mock_response

        bugzilla_id = make_bugzilla_call("/url/", {})
        self.assertIsNone(bugzilla_id)

        mock_logging.info.assert_called_with(
            (
                "Error creating Bugzilla Ticket: "
                "Error creating Bugzilla Bug because of reasons"
            )
        )

    def test_request_error_passes_silently(self):
        self.mock_bugzilla_requests_post.side_effect = RequestException()
        bugzilla_id = make_bugzilla_call("/url/", {})
        self.assertIsNone(bugzilla_id)

    def test_json_parse_error_passes_silently(self):
        mock_response = mock.Mock()
        mock_response.content = "{invalid json"
        self.mock_bugzilla_requests_post.return_value = mock_response
        bugzilla_id = make_bugzilla_call("/url/", {})
        self.assertIsNone(bugzilla_id)
