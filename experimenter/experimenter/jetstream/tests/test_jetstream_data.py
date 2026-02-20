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

    def test_append_days_3_retention_extracts_data(self):
        retention = JetstreamDataPoint(
            metric=Metric.DAYS_3_RETENTION,
            statistic=Statistic.BINOMIAL,
            branch="control",
            point=0.65,
            segment=Segment.ALL,
        )

        data = JetstreamData([])
        data.append_days_3_retention([retention])

        self.assertIn(retention, data)
