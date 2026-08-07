from django.test import TestCase

from experimenter.jetstream.models import (
    JetstreamData,
    JetstreamDataPoint,
    Metric,
    Segment,
    Statistic,
)
from experimenter.jetstream.tests.constants import JetstreamTestData


class TestJetstreamData(TestCase):
    def test_append_population_percentages(self):
        # setup JetstreamData with duplicate identity points
        identity = JetstreamTestData.get_identity_row()
        control_identity = identity.model_copy()
        control_identity.branch = "control"

        variant_identity = identity.model_copy()
        variant_identity.branch = "variant"

        data = JetstreamData(
            [control_identity, variant_identity, control_identity, variant_identity]
        )

        # append population percentages
        data.append_population_percentages()

        # verify percentages are as expected
        expected_control = JetstreamDataPoint(
            metric=Metric.USER_COUNT,
            statistic=Statistic.PERCENT,
            branch="control",
            point=50,
            segment=Segment.ALL,
        )
        expected_variant = JetstreamDataPoint(
            metric=Metric.USER_COUNT,
            statistic=Statistic.PERCENT,
            branch="variant",
            point=50,
            segment=Segment.ALL,
        )

        self.assertIn(expected_control, data)
        self.assertIn(expected_variant, data)

    def test_append_retention_3_days_extracts_data(self):
        retention = JetstreamDataPoint(
            metric=Metric.RETENTION_3_DAYS,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.65,
            segment=Segment.ALL,
            window_index="4",
        )

        data = JetstreamData([])
        data.append_retention_3_days([retention])

        self.assertIn(retention, data)

    def test_remove_retention_data(self):
        retained = JetstreamDataPoint(
            metric=Metric.RETENTION,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.65,
            segment=Segment.ALL,
        )
        identity = JetstreamTestData.get_identity_row()
        data = JetstreamData([retained, identity])

        data.remove_retention_data()

        self.assertEqual(data.root, [identity])

    def test_separate_weekly_retention_data_splits_retention_by_week(self):
        weekly_data = JetstreamData(
            [
                JetstreamDataPoint(
                    metric=Metric.RETENTION,
                    statistic=Statistic.BINOMIAL,
                    branch="control",
                    point=week / 10,
                    segment=Segment.ALL,
                    window_index=str(week),
                )
                for week in (1, 2, 3, 4, 5, 6)
            ]
        )
        transformed_data = JetstreamData([])

        transformed_data.separate_weekly_retention_data(weekly_data)

        self.assertEqual(
            [
                (point.metric, point.window_index, point.point)
                for point in transformed_data
            ],
            [
                (Metric.WEEKLY_RETENTION.format(2), "2", 0.2),
                (Metric.WEEKLY_RETENTION.format(3), "3", 0.3),
                (Metric.WEEKLY_RETENTION.format(4), "4", 0.4),
                (Metric.WEEKLY_RETENTION.format(5), "5", 0.5),
                (Metric.WEEKLY_RETENTION.format(6), "6", 0.6),
            ],
        )

    def test_replace_retention_3_days_replaces_existing_entries(self):
        existing_retention_1 = JetstreamDataPoint(
            metric=Metric.RETENTION_3_DAYS,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.5,
            segment=Segment.ALL,
            window_index="1",
        )
        existing_retention_2 = JetstreamDataPoint(
            metric=Metric.RETENTION_3_DAYS,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.25,
            segment=Segment.ALL,
            window_index="2",
        )
        existing_retention_3 = JetstreamDataPoint(
            metric=Metric.RETENTION_3_DAYS,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.25,
            segment=Segment.ALL,
            window_index="3",
        )
        kept_retention = JetstreamDataPoint(
            metric=Metric.RETENTION_3_DAYS,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.65,
            segment=Segment.ALL,
            window_index="4",
        )

        data = JetstreamData(
            [
                existing_retention_1,
                existing_retention_2,
                existing_retention_3,
                kept_retention,
            ]
        )
        data.replace_retention_3_days(data)

        self.assertNotIn(existing_retention_1, data)
        self.assertNotIn(existing_retention_2, data)
        self.assertNotIn(existing_retention_3, data)
        self.assertIn(kept_retention, data)

    def test_replace_retention_3_days_handles_legacy_metric_name(self):
        existing_retention = JetstreamDataPoint(
            metric=Metric.RETENTION_3_DAYS_LEGACY,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.25,
            segment=Segment.ALL,
            window_index="1",
        )
        kept_retention = JetstreamDataPoint(
            metric=Metric.RETENTION_3_DAYS_LEGACY,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.65,
            segment=Segment.ALL,
            window_index="4",
        )

        data = JetstreamData([existing_retention, kept_retention])
        data.replace_retention_3_days(data)

        self.assertNotIn(existing_retention, data)
        self.assertIn(kept_retention, data)
