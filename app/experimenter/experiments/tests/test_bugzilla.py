import mock
import requests
from django.test import TestCase
from django.conf import settings

from experimenter.experiments.models import Experiment
from experimenter.experiments.bugzilla import (
    BugzillaError,
    create_experiment_bug,
    format_bug_body,
    make_bugzilla_call,
    update_experiment_bug,
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
                experiment.bugzilla_tracking_key: "?",
            },
        )

    def test_create_bugzilla_ticket_creation_with_bad_assigned_to_val(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        self.setUpMockBugzillaInvalidUser()

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

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
            "cc": settings.BUGZILLA_CC_LIST,
            "type": "task",
            "priority": "P3",
            "see_also": [12345],
            "blocks": [12345],
            "url": experiment.experiment_url,
            experiment.bugzilla_tracking_key: "?",
        }

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )

    def test_create_bugzilla_ticket_creation_with_see_also_bad_val(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        self.setUpMockBugzillaFirstBadTicket()

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

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
            "url": experiment.experiment_url,
            experiment.bugzilla_tracking_key: "?",
            "blocks": [12345],
        }

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )

    def test_create_bugzilla_ticket_creation_with_blocks_bad_val(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        self.setUpMockBugzillaSecondBadTicket()

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

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
            "url": experiment.experiment_url,
            experiment.bugzilla_tracking_key: "?",
            "see_also": [12345],
        }

        self.mock_bugzilla_requests_post.assert_called_with(
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
            firefox_version="55.0",
            firefox_channel="Beta",
        )

        update_experiment_bug(experiment)
        summary = "[Experiment] Pref-Flip: An Experiment Fx 55.0 Beta".format(
            exp_name=experiment,
            version=experiment.firefox_version,
            channel=experiment.firefox_channel,
        )

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            {"summary": summary, "cf_user_story": format_bug_body(experiment)},
        )

    def test_update_bugzilla_addon_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_ADDON,
            firefox_version="56.0",
            firefox_channel="Nightly",
        )
        update_experiment_bug(experiment)
        summary = "[Experiment] Add-On: An Experiment Fx 56.0 Nightly".format(
            exp_name=experiment,
            version=experiment.firefox_version,
            channel=experiment.firefox_channel,
        )

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            {"summary": summary, "cf_user_story": format_bug_body(experiment)},
        )


class TestMakeBugzillaCall(MockBugzillaMixin, TestCase):

    def test_api_error_logs_message(self):
        mock_response_data = {
            "message": "Error creating Bugzilla Bug because of reasons"
        }
        mock_response = mock.Mock()
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 400
        self.mock_bugzilla_requests_post.return_value = mock_response

        response_data = make_bugzilla_call("/url/", requests.post, data={})
        self.assertEqual(response_data, mock_response_data)

    def test_json_parse_error_raises_bugzilla_error(self):
        self.mock_bugzilla_requests_post.side_effect = ValueError()

        with self.assertRaises(BugzillaError):
            make_bugzilla_call("/url/", requests.post, data={})


class TestMakePutBugzillaCall(MockBugzillaMixin, TestCase):

    def test_api_error_logs_message(self):
        mock_response_data = {"message": "Error: Something went wrong"}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 400
        self.mock_bugzilla_requests_put.return_value = mock_response

        response_data = make_bugzilla_call("/url/", requests.put, data={})
        self.assertEqual(response_data, mock_response_data)

    def test_json_parse_error_raises_bugzilla_error(self):
        self.mock_bugzilla_requests_put.side_effect = ValueError()
        with self.assertRaises(BugzillaError):
            make_bugzilla_call("/url/", requests.put, data={})
