import mock
from django.test import TestCase
from django.utils import timezone

from experimenter.experiments.models import (
    Experiment,
    ExperimentChangeLog,
    NimbusExperiment,
)
from experimenter.experiments.tests.factories.legacy import (
    ExperimentChangeLogFactory,
    ExperimentFactory,
)
from experimenter.experiments.tests.factories.nimbus import (
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
)
from experimenter.normandy.tests.mixins import MockNormandyMixin
from experimenter.reporting.constants import ReportLogConstants
from experimenter.reporting.models import ReportLog
from experimenter.reporting.tasks import (
    create_reportlog,
    generate_reportlogs,
    get_event_reason,
    get_event_type,
    get_experiment_type,
    is_duplicate_recipe_change,
)
from experimenter.reporting.tests.factories import ReportLogFactory


class TestTask(MockNormandyMixin, TestCase):
    def test_get_experiment_type_formats_normandy_exp_properly(self):
        exp = ExperimentFactory.create(type=Experiment.TYPE_PREF)
        reportlog_type = get_experiment_type(exp)
        self.assertEqual(reportlog_type, "Normandy-Pref")

    def test_get_experiment_type_formats_nimbus_exp_properly(self):
        exp = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        reportlog_type = get_experiment_type(exp)
        self.assertEqual(reportlog_type, "Nimbus-Firefox-Desktop")

    def test_get_event_type_returns_create(self):
        change_log = ExperimentChangeLogFactory.create(
            old_status=None, new_status=Experiment.STATUS_DRAFT
        )
        event = get_event_type(change_log)
        self.assertEqual(str(event), "Create")

    def test_get_event_type_returns_complete(self):
        change_log = NimbusChangeLogFactory.create(
            old_status="Live", new_status="Complete"
        )
        event = get_event_type(change_log)
        self.assertEqual(str(event), "End")

    def test_get_event_type_returns_update(self):
        change_log = ExperimentChangeLogFactory.create(
            old_status="Live", new_status="Live"
        )
        event = get_event_type(change_log)
        self.assertEqual(str(event), "Update")

    def test_get_event_reason_returns_new(self):
        event = ReportLogConstants.Event.CREATE
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_DRAFT
        )
        create_log = experiment.changes.first()
        reason = get_event_reason(create_log, event)
        self.assertEqual(str(reason), "New")

    def test_get_create_event_reason_returns_clone(self):
        parent = ExperimentFactory.create()
        experiment = ExperimentFactory.create(parent=parent)
        event = ReportLogConstants.Event.CREATE
        create_log = ExperimentChangeLogFactory.create(
            message="Cloned Experiment", experiment=experiment
        )
        reason = get_event_reason(create_log, event)
        self.assertEqual(str(reason), "Clone")

    def test_get_end_event_reason_returns_message_as_reason(self):
        event = ReportLogConstants.Event.END
        message = "Enrollment Issue"
        end_log = ExperimentChangeLogFactory.create(
            old_status="Live", new_status="Complete", message=message
        )
        reason = get_event_reason(end_log, event)
        self.assertEqual(reason, message)

    def test_end_event_reason_returns_experiment_complete(self):
        event = ReportLogConstants.Event.END
        end_log = NimbusChangeLogFactory.create(
            old_status="Live", new_status="Complete", message=None
        )
        reason = get_event_reason(end_log, event)
        self.assertEqual(str(reason), "Experiment Complete")

    def test_get_update_event_reason_returns_qa_launch(self):
        event = ReportLogConstants.Event.UPDATE
        changelog = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_ACCEPTED, new_status=Experiment.STATUS_ACCEPTED
        )
        event_reason = get_event_reason(changelog, event)
        self.assertEqual(event_reason, ReportLogConstants.EventReason.QA_LAUNCH)

    def test_get_update_event_reason_returns_launch(self):
        event = ReportLogConstants.Event.UPDATE
        changelog = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_ACCEPTED, new_status=Experiment.STATUS_LIVE
        )
        event_reason = get_event_reason(changelog, event)
        self.assertEqual(event_reason, ReportLogConstants.EventReason.LAUNCH)

    def test_get_update_event_reason_returns_status_change(self):
        event = ReportLogConstants.Event.UPDATE
        changelog = NimbusChangeLogFactory.create(
            old_status="Draft", new_status="Preview"
        )
        event_reason = get_event_reason(changelog, event)
        self.assertEqual(event_reason, ReportLogConstants.EventReason.STATUS_CHANGE)

    def test_get_update_event_reason_returns_recipe_change(self):
        event = ReportLogConstants.Event.UPDATE
        changelog = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_LIVE,
            new_status=Experiment.STATUS_LIVE,
            message="Added Version(s)",
        )
        event_reason = get_event_reason(changelog, event)
        self.assertEqual(event_reason, ReportLogConstants.EventReason.RECIPE_CHANGE)

    def test_get_update_event_reason_returns_pause(self):
        event = ReportLogConstants.Event.UPDATE
        changelog = ExperimentChangeLogFactory.create(
            old_status=Experiment.STATUS_LIVE,
            new_status=Experiment.STATUS_LIVE,
            message="Enrollment Complete",
        )
        event_reason = get_event_reason(changelog, event)
        self.assertEqual(event_reason, ReportLogConstants.EventReason.PAUSE)

    def test_is_duplicate_recipe_change_returns_true(self):
        experiment = ExperimentFactory.create()
        report_log = ReportLogFactory.create(
            timestamp=timezone.now(),
            experiment_type="Normandy-Pref",
            experiment_name=experiment.name,
            experiment_old_status=Experiment.STATUS_LIVE,
            experiment_new_status=Experiment.STATUS_LIVE,
            event=ReportLogConstants.Event.UPDATE,
            event_reason=ReportLogConstants.EventReason.RECIPE_CHANGE,
        )

        later = timezone.now() + timezone.timedelta(hours=1)
        self.assertTrue(
            is_duplicate_recipe_change(later, experiment, report_log.event_reason)
        )

    def test_create_reportlog_creates_a_create_reportlog(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_DRAFT, type=Experiment.TYPE_PREF
        )
        changelog = experiment.changes.first()
        create_reportlog(experiment.changes.first())
        report_log = ReportLog.objects.all()[0]
        self.assertEqual(report_log.timestamp, changelog.changed_on)
        self.assertEqual(report_log.experiment_slug, experiment.slug)
        self.assertEqual(report_log.experiment_type, "Normandy-Pref")
        self.assertEqual(report_log.event_reason, "New")
        self.assertEqual(report_log.event, "Create")

    def test_generate_reportlogs_creates_for_both_types_of_changelogs(self):
        mock_response_data = []
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200
        self.mock_normandy_requests_get.return_value = mock_response
        ExperimentFactory.create_with_status(target_status=Experiment.STATUS_LIVE)
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        self.assertEqual(ReportLog.objects.count(), 0)
        generate_reportlogs()
        self.assertEqual(
            ReportLog.objects.filter(experiment_type__startswith="Normandy").count(), 5
        )
        self.assertEqual(
            ReportLog.objects.filter(experiment_type__startswith="Nimbus").count(), 3
        )
        self.assertEqual(ReportLog.objects.count(), 8)

        ExperimentChangeLogFactory.create(changed_on=timezone.now())

        self.assertEqual(ExperimentChangeLog.objects.count(), 6)
        generate_reportlogs()

        # Disable until https://github.com/mozilla/experimenter/issues/5976 lands
        # self.assertEqual(ReportLog.objects.count(), 9)

    def test_generate_reportlogs_creates_for_normandy_changes(self):
        mock_response_data = [
            {"updated": "2021-06-15T18:59:06.681707Z"},
            {"updated": "2021-06-15T18:59:07.681707Z"},
            {"updated": "2021-06-15T18:59:08.681707Z"},
        ]
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200
        self.mock_normandy_requests_get.return_value = mock_response
        ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_LIVE, normandy_id=1234
        )

        self.assertEqual(ReportLog.objects.count(), 0)
        generate_reportlogs()
        self.assertEqual(ReportLog.objects.count(), 6)
