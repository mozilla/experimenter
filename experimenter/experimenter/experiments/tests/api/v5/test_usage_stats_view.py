import csv
import datetime
import io

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.models import NimbusChangeLog, NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory

LIFECYCLE = NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE


def _create_experiment(owner, start_date):
    return NimbusExperimentFactory.create_with_lifecycle(
        LIFECYCLE,
        start_date=start_date,
        end_date=start_date + datetime.timedelta(days=28),
        owner=owner,
    )


class TestNimbusExperimentUsageStatsView(TestCase):
    def _get_csv_rows(self):
        response = self.client.get(
            reverse("nimbus-experiments-csv-usage"),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        content = response.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)

    @staticmethod
    def _month_index(year, month):
        return (year - 2020) * 12 + (month - 1)

    def test_empty_database_returns_empty_csv(self):
        response = self.client.get(
            reverse("nimbus-experiments-csv-usage"),
            **{settings.OPENIDC_EMAIL_HEADER: "user@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "")

    def test_single_experiment_counts_owner(self):
        owner = UserFactory.create(email="owner1@example.com")
        _create_experiment(owner, datetime.date(2023, 3, 15))

        rows = self._get_csv_rows()

        self.assertEqual(len(rows), 52)
        self.assertEqual(rows[0]["Month"], "2020-01")

        march = rows[self._month_index(2023, 3)]
        self.assertEqual(march["Month"], "2023-03")
        self.assertEqual(march["Owners"], "1")
        self.assertEqual(march["Novice (0-3)"], "1")
        self.assertEqual(march["Intermediate (4-9)"], "0")
        self.assertEqual(march["Advanced (10+)"], "0")

    def test_cumulative_owners_across_months(self):
        owner1 = UserFactory.create(email="owner1@example.com")
        owner2 = UserFactory.create(email="owner2@example.com")

        _create_experiment(owner1, datetime.date(2023, 1, 10))
        _create_experiment(owner2, datetime.date(2023, 3, 10))

        rows = self._get_csv_rows()

        self.assertEqual(rows[self._month_index(2023, 1)]["Owners"], "1")
        self.assertEqual(rows[self._month_index(2023, 2)]["Owners"], "1")
        self.assertEqual(rows[self._month_index(2023, 3)]["Owners"], "2")

    def test_reviewer_counted_from_approval_changelog(self):
        owner = UserFactory.create(email="owner@example.com")
        reviewer = UserFactory.create(email="reviewer@example.com")

        experiment = _create_experiment(owner, datetime.date(2023, 6, 1))

        rows = self._get_csv_rows()
        self.assertEqual(rows[self._month_index(2023, 6)]["Reviewers"], "1")

        NimbusChangeLog.objects.create(
            experiment=experiment,
            changed_by=reviewer,
            old_status=NimbusExperiment.Status.DRAFT,
            new_status=NimbusExperiment.Status.DRAFT,
            old_publish_status=NimbusExperiment.PublishStatus.REVIEW,
            new_publish_status=NimbusExperiment.PublishStatus.APPROVED,
        )

        rows = self._get_csv_rows()
        self.assertEqual(rows[self._month_index(2023, 6)]["Reviewers"], "2")

    def test_experience_levels_advance_with_experiment_count(self):
        owner = UserFactory.create(email="prolific@example.com")

        for i in range(12):
            _create_experiment(
                owner,
                datetime.date(2023, 1, 1) + datetime.timedelta(days=30 * i),
            )

        rows = self._get_csv_rows()

        jan = rows[self._month_index(2023, 1)]
        self.assertEqual(jan["Novice (0-3)"], "1")
        self.assertEqual(jan["Intermediate (4-9)"], "0")

        apr = rows[self._month_index(2023, 4)]
        self.assertEqual(apr["Novice (0-3)"], "0")
        self.assertEqual(apr["Intermediate (4-9)"], "1")

        oct_row = rows[self._month_index(2023, 10)]
        self.assertEqual(oct_row["Intermediate (4-9)"], "0")
        self.assertEqual(oct_row["Advanced (10+)"], "1")

    def test_quarterly_rollups(self):
        owner = UserFactory.create(email="owner@example.com")
        _create_experiment(owner, datetime.date(2023, 6, 1))

        rows = self._get_csv_rows()

        self.assertEqual(len(rows), 56)
        self.assertEqual(rows[42]["Month"], "2020 Q1")
        self.assertEqual(rows[42]["Owners"], "0")

        self.assertEqual(rows[-1]["Month"], "2023 Q2")
        self.assertEqual(rows[-1]["Owners"], "1")
