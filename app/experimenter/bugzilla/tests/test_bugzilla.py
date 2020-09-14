import mock
import requests
from django.conf import settings
from django.test import TestCase

from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.bugzilla import (
    BugzillaError,
    add_experiment_comment,
    create_experiment_bug,
    format_bug_body,
    format_summary,
    get_bugzilla_id,
    make_bugzilla_call,
    set_bugzilla_id_value,
    update_bug_resolution,
    update_experiment_bug,
)
from experimenter.bugzilla.tests.mixins import MockBugzillaMixin
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import ExperimentFactory


class TestCreateExperimentBug(MockBugzillaMixin, TestCase):
    def test_get_bugzilla_id_with_valid_bug_id(self):
        bug_url = "https://bugzilla.allizom.org/show_bug.cgi?id=1234"
        bug_id = get_bugzilla_id(bug_url)
        self.assertEqual(bug_id, 1234)

    def test_get_bugzilla_id_with_bad_bug_id(self):
        bug_url = "https://bugzilla.allizom.org/show_bug.cgi?id=1234ssss"
        self.assertIsNone(set_bugzilla_id_value(bug_url))

    def test_creating_pref_bugzilla_ticket_returns_ticket_id(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            firefox_min_version="56.0",
            firefox_max_version="57.0",
        )

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_CREATE_URL,
            {
                "product": "Shield",
                "component": "Shield Study",
                "version": "unspecified",
                "summary": "[Experiment]: {experiment}".format(experiment=experiment),
                "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
                    experiment=experiment
                ),
                "cc": settings.BUGZILLA_CC_LIST,
                "type": "task",
                "priority": "P3",
                "assigned_to": experiment.owner.email,
                "blocks": [12345],
                "url": experiment.experiment_url,
            },
        )

    def test_create_bugzilla_ticket_creation_with_bad_assigned_to_val(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        self.mock_bugzilla_requests_get.side_effect = [
            self.buildMockFailureResponse(),
            self.buildMockSuccessBugResponse(),
        ]

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

        expected_call_data = {
            "product": "Shield",
            "component": "Shield Study",
            "version": "unspecified",
            "summary": "[Experiment]: {experiment}".format(experiment=experiment),
            "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
                experiment=experiment
            ),
            "cc": settings.BUGZILLA_CC_LIST,
            "type": "task",
            "priority": "P3",
            "assigned_to": None,
            "blocks": [12345],
            "url": experiment.experiment_url,
        }

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )

    def test_create_bugzilla_ticket_creation_with_blocks_bad_val(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, name="An Experiment"
        )

        self.mock_bugzilla_requests_get.side_effect = [
            self.buildMockSuccessUserResponse(),
            self.buildMockFailureResponse(),
            self.buildMockSuccessResponse(),
        ]

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

        expected_call_data = {
            "product": "Shield",
            "component": "Shield Study",
            "version": "unspecified",
            "summary": "[Experiment]: {experiment}".format(experiment=experiment),
            "description": experiment.BUGZILLA_OVERVIEW_TEMPLATE.format(
                experiment=experiment
            ),
            "assigned_to": experiment.owner.email,
            "cc": settings.BUGZILLA_CC_LIST,
            "type": "task",
            "priority": "P3",
            "url": experiment.experiment_url,
            "blocks": None,
        }

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_CREATE_URL, expected_call_data
        )

    def test_create_bugzilla_ticket_creation_for_rapid_experiments(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID, name="An Experiment"
        )

        self.mock_bugzilla_requests_get.side_effect = [
            self.buildMockSuccessUserResponse(),
            self.buildMockSuccessResponse(),
        ]

        response_data = create_experiment_bug(experiment)

        self.assertEqual(response_data, self.bugzilla_id)

        expected_call_data = {
            "product": "Shield",
            "component": "Shield Study",
            "version": "unspecified",
            "type": "task",
            "summary": "[Experiment]: {experiment}".format(experiment=experiment),
            "description": experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE,
            "assigned_to": experiment.owner.email,
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

    def test_format_long_summary_name(self):
        long_name = "a" * 225
        experiment = ExperimentFactory.create(name=long_name)
        summary = format_summary(experiment)

        expected_name = "a" * 150

        expected_summary = ("[Experiment]: Pref-Flip Experiment: {name}...").format(
            name=expected_name
        )
        self.assertEqual(summary, expected_summary)


class TestFormatBugBody(TestCase):
    def test_countries_locales_list_all_when_none_specified(self):
        experiment = ExperimentFactory.create(countries=[], locales=[])
        body = format_bug_body(experiment)
        self.assertIn("Countries: all", body)
        self.assertIn("Locales: all", body)

    def test_format_bug_body_lists_countries_locales(self):
        country = CountryFactory(code="CA", name="Canada")
        locale = LocaleFactory(code="da", name="Danish")
        experiment = ExperimentFactory.create(countries=[country], locales=[locale])
        body = format_bug_body(experiment)
        self.assertIn("Countries: Canada (CA)", body)
        self.assertIn("Locales: Danish (da)", body)


class TestUpdateExperimentBug(MockBugzillaMixin, TestCase):
    def test_update_bugzilla_pref_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_PREF,
            firefox_min_version="55.0",
            firefox_max_version="56.0",
            firefox_channel="Beta",
        )

        update_experiment_bug(experiment)
        summary = "[Experiment] Pref-Flip Experiment: An Experiment Fx 55.0 to 56.0 Beta"

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
            firefox_min_version="56.0",
            firefox_max_version="",
            firefox_channel="Nightly",
        )
        update_experiment_bug(experiment)
        summary = "[Experiment] Add-On Experiment: An Experiment Fx 56.0 Nightly"

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            {"summary": summary, "cf_user_story": format_bug_body(experiment)},
        )


class TestUpdateBugzillaResolution(MockBugzillaMixin, TestCase):
    def test_bugzilla_resolution_with_archive_true(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_PREF,
            archived=True,
        )

        update_bug_resolution(experiment)
        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            {"status": "RESOLVED", "resolution": "WONTFIX"},
        )

    def test_bugzilla_resolution_with_archive_false(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_PREF,
            archived=False,
        )

        update_bug_resolution(experiment)

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            {"status": "REOPENED"},
        )

    def test_bugzilla_resolution_with_completed_status(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_COMPLETE)

        update_bug_resolution(experiment)

        self.mock_bugzilla_requests_put.assert_called_with(
            settings.BUGZILLA_UPDATE_URL.format(id=experiment.bugzilla_id),
            {"status": "RESOLVED", "resolution": "FIXED"},
        )


class TestAddExperimentComment(MockBugzillaMixin, TestCase):
    def test_add_bugzilla_comment_pref_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_PREF,
        )
        comment = "Start Date: {} End Date: {}".format(
            experiment.start_date, experiment.end_date
        )

        comment_id = add_experiment_comment(experiment.bugzilla_id, comment)

        self.assertEqual(comment_id, self.bugzilla_id)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
            {"comment": comment},
        )

    def test_add_bugzilla_comment_addon_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            name="An Experiment",
            bugzilla_id="123",
            type=Experiment.TYPE_ADDON,
        )

        comment = "Start Date: {} End Date: {}".format(
            experiment.start_date, experiment.end_date
        )

        comment_id = add_experiment_comment(experiment.bugzilla_id, comment)

        self.assertEqual(comment_id, self.bugzilla_id)

        self.mock_bugzilla_requests_post.assert_called_with(
            settings.BUGZILLA_COMMENT_URL.format(id=experiment.bugzilla_id),
            {"comment": comment},
        )


class TestMakeBugzillaCall(MockBugzillaMixin, TestCase):
    def test_api_error_logs_message(self):
        mock_response_data = {"message": "Error creating Bugzilla Bug because of reasons"}
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
