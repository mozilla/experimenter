import json

import mock
from requests.exceptions import RequestException
from django.test import TestCase
from django.conf import settings

from experimenter.experiments.models import Experiment
from experimenter.experiments.bugzilla import (
    BugzillaError,
    add_experiment_comment,
    create_experiment_bug,
    format_bug_body,
    make_bugzilla_call,
)
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.tests.mixins import MockBugzillaMixin


class TestCreateExperimentBug(MockBugzillaMixin, TestCase):

    def test_creating_pref_bugzilla_ticket_returns_ticket_id(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

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

    def test_create_bugzilla_ticket_retries_with_no_assignee(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        self.setUpMockBugzillaInvalidUser()

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)
        self.assertEqual(self.mock_bugzilla_requests_post.call_count, 2)

        expected_call_data = {
            "product": "Shield",
            "component": "Shield Study",
            "version": "unspecified",
            "summary": "[Shield] {experiment}".format(experiment=experiment),
            "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
                experiment=experiment
            ),
            "assigned_to": experiment.owner.email,
            "cc": settings.BUGZILLA_CC_LIST,
        }

        self.mock_bugzilla_requests_post.assert_any_call(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )

        del expected_call_data["assigned_to"]

        self.mock_bugzilla_requests_post.assert_any_call(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )


class TestAddExperimentComment(MockBugzillaMixin, TestCase):

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


class TestMakeBugzillaCall(MockBugzillaMixin, TestCase):

    def test_api_error_logs_message(self):
        mock_response_data = {
            "message": "Error creating Bugzilla Bug because of reasons"
        }
        mock_response = mock.Mock()
        mock_response.content = json.dumps(mock_response_data)
        mock_response.status_code = 400
        self.mock_bugzilla_requests_post.return_value = mock_response

        response_data = make_bugzilla_call("/url/", {})
        self.assertEqual(response_data, mock_response_data)

    def test_request_error_passes_silently(self):
        self.mock_bugzilla_requests_post.side_effect = RequestException()

        with self.assertRaises(BugzillaError):
            make_bugzilla_call("/url/", {})

    def test_json_parse_error_passes_silently(self):
        mock_response = mock.Mock()
        mock_response.content = "{invalid json"
        self.mock_bugzilla_requests_post.return_value = mock_response
        with self.assertRaises(BugzillaError):
            make_bugzilla_call("/url/", {})
