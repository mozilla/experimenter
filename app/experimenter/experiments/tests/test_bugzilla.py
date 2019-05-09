import json

import mock
from requests.exceptions import RequestException
from django.test import TestCase
from django.conf import settings

from experimenter.experiments.models import Experiment
from experimenter.experiments.bugzilla import (
    BugzillaError,
    create_experiment_bug,
    format_bug_body,
    make_bugzilla_post_call,
    get_firefox_major_version,
    update_experiment_bug,
    make_bugzilla_put_call,
)
from experimenter.experiments.tests.factories import ExperimentFactory
from experimenter.experiments.tests.mixins import MockBugzillaMixin


class TestCreateExperimentBug(MockBugzillaMixin, TestCase):

    def test_creating_pref_bugzilla_ticket_returns_ticket_id(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            firefox_version="56.0",
        )

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_CREATE_URL,
            {
                "product": "Shield",
                "component": "Shield Study",
                "version": "unspecified",
                "summary": "[Experiment]: {experiment}".format(
                    experiment=experiment
                ),
                "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
                    experiment=experiment
                ),
                "assigned_to": experiment.owner.email,
                "cc": settings.BUGZILLA_CC_LIST,
                "type": "task",
                "priority": "P3",
                "see_also": [12345],
                "blocks": [12345],
                "url": experiment.experiment_url,
                "whiteboard": experiment.STATUS_REVIEW_LABEL,
                experiment.bugzilla_tracking_key: "?",
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
            "summary": "[Experiment]: {experiment}".format(
                experiment=experiment
            ),
            "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
                experiment=experiment
            ),
            "assigned_to": experiment.owner.email,
            "cc": settings.BUGZILLA_CC_LIST,
            "type": "task",
            "priority": "P3",
            "see_also": [12345],
            "blocks": [12345],
            "url": experiment.experiment_url,
            "whiteboard": experiment.STATUS_REVIEW_LABEL,
            experiment.bugzilla_tracking_key: "?",
        }

        self.mock_bugzilla_requests_post.assert_any_call(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )

        del expected_call_data["assigned_to"]

        self.mock_bugzilla_requests_post.assert_any_call(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )

    def test_create_bugzilla_ticket_retries_with_no_cf_tracking(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )
        self.setUpMockBugzillaInvalidFirefoxVersion()

        bugzilla_id = create_experiment_bug(experiment)

        self.assertEqual(bugzilla_id, self.bugzilla_id)
        self.assertEqual(self.mock_bugzilla_requests_post.call_count, 2)

        expected_call_data = {
            "product": "Shield",
            "component": "Shield Study",
            "version": "unspecified",
            "summary": "[Experiment]: {experiment}".format(
                experiment=experiment
            ),
            "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
                experiment=experiment
            ),
            "assigned_to": experiment.owner.email,
            "cc": settings.BUGZILLA_CC_LIST,
            "type": "task",
            "priority": "P3",
            "see_also": [12345],
            "blocks": [12345],
            "url": experiment.experiment_url,
            "whiteboard": experiment.STATUS_REVIEW_LABEL,
        }

        self.mock_bugzilla_requests_post.assert_any_call(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )

    def test_create_bugzilla_ticket_creation_failure(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )
        self.setupMockBugzillaCreationFailure()
        self.assertRaises(BugzillaError, create_experiment_bug, experiment)


class TestUpdateExperimentBug(MockBugzillaMixin, TestCase):

    def test_update_bugzilla_pref_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_PREF,
        )
        cf_tracking = "cf_tracking_firefox{}".format(
            get_firefox_major_version(experiment.firefox_version)
        )

        update_experiment_bug(experiment)
        summary = "[Experiment] {exp_name} Fx {version} {channel}".format(
            exp_name=experiment,
            version=experiment.firefox_version,
            channel=experiment.firefox_channel,
        )

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            {
                "summary": summary,
                "cf_user_story": format_bug_body(experiment),
                "whiteboard": experiment.STATUS_SHIP_LABEL,
                cf_tracking: "?",
            },
        )

    def test_update_bugzilla_addon_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_ADDON,
        )
        cf_tracking = "cf_tracking_firefox{}".format(
            get_firefox_major_version(experiment.firefox_version)
        )

        update_experiment_bug(experiment)
        summary = "[Experiment] {exp_name} Fx {version} {channel}".format(
            exp_name=experiment,
            version=experiment.firefox_version,
            channel=experiment.firefox_channel,
        )

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            {
                "summary": summary,
                "cf_user_story": format_bug_body(experiment),
                "whiteboard": experiment.STATUS_SHIP_LABEL,
                cf_tracking: "?",
            },
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

        response_data = make_bugzilla_post_call("/url/", {})
        self.assertEqual(response_data, mock_response_data)

    def test_request_error_passes_silently(self):
        self.mock_bugzilla_requests_post.side_effect = RequestException()

        with self.assertRaises(BugzillaError):
            make_bugzilla_post_call("/url/", {})

    def test_json_parse_error_passes_silently(self):
        mock_response = mock.Mock()
        mock_response.content = "{invalid json"
        self.mock_bugzilla_requests_post.return_value = mock_response
        with self.assertRaises(BugzillaError):
            make_bugzilla_post_call("/url/", {})


class TestMakePutBugzillaCall(MockBugzillaMixin, TestCase):

    def test_api_error_logs_message(self):
        mock_response_data = {"message": "Error: Something went wrong"}
        mock_response = mock.Mock()
        mock_response.content = json.dumps(mock_response_data)
        mock_response.status_code = 400
        self.mock_bugzilla_requests_put.return_value = mock_response

        response_data = make_bugzilla_put_call("/url/", {})
        self.assertEqual(response_data, mock_response_data)

    def test_json_parse_error_passes_silently(self):
        mock_response = mock.Mock()
        mock_response.content = "{invalid json"
        self.mock_bugzilla_requests_put.return_value = mock_response
        with self.assertRaises(BugzillaError):
            make_bugzilla_put_call("/url/", {})
