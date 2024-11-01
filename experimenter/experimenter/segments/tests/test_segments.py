from django.core.checks import Error
from django.test import TestCase

from experimenter.experiments.models import NimbusExperiment
from experimenter.segments import Segment, Segments, check_segments
from experimenter.segments.tests import mock_get_invalid_segments, mock_get_segments


class TestSegments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Segments.clear_cache()

    def test_load_all_segments(self):
        segments = Segments.all(mock_get_segments())
        self.assertEqual(len(segments), 4)

        self.assertIn(
            Segment(
                slug="fenix_segment",
                friendly_name="Fenix Segment",
                application=NimbusExperiment.Application.FENIX,
                description="Fenix segment for testing",
                select_expression="{{agg_sum('ad_click')}}",
            ),
            segments,
        )

        self.assertIn(
            Segment(
                slug="desktop_segment_1",
                friendly_name="Desktop Segment 1",
                application=NimbusExperiment.Application.DESKTOP,
                description="Firefox desktop segment used for testing",
                select_expression="country_code in ('IN', 'US')",
            ),
            segments,
        )

        self.assertIn(
            Segment(
                slug="desktop_segment_2",
                friendly_name="Desktop Segment 2",
                application=NimbusExperiment.Application.DESKTOP,
                description="",
                select_expression="country_code in ('IN', 'US')",
            ),
            segments,
        )

        self.assertIn(
            Segment(
                slug="desktop_segment_3",
                friendly_name="Desktop Segment 3",
                application=NimbusExperiment.Application.DESKTOP,
                description="Firefox desktop segment used for testing",
                select_expression="",
            ),
            segments,
        )

    def test_load_segments_by_application(self):
        fenix_segments = Segments.by_application(
            NimbusExperiment.Application.FENIX, mock_get_segments()
        )
        self.assertEqual(len(fenix_segments), 1)
        self.assertIn(
            Segment(
                slug="fenix_segment",
                friendly_name="Fenix Segment",
                application=NimbusExperiment.Application.FENIX,
                description="Fenix segment for testing",
                select_expression="{{agg_sum('ad_click')}}",
            ),
            fenix_segments,
        )

        desktop_segments = Segments.by_application(
            NimbusExperiment.Application.DESKTOP, mock_get_segments()
        )
        self.assertEqual(len(desktop_segments), 3)
        self.assertIn(
            Segment(
                slug="desktop_segment_1",
                friendly_name="Desktop Segment 1",
                application=NimbusExperiment.Application.DESKTOP,
                description="Firefox desktop segment used for testing",
                select_expression="country_code in ('IN', 'US')",
            ),
            desktop_segments,
        )
        self.assertIn(
            Segment(
                slug="desktop_segment_2",
                friendly_name="Desktop Segment 2",
                application=NimbusExperiment.Application.DESKTOP,
                description="",
                select_expression="country_code in ('IN', 'US')",
            ),
            desktop_segments,
        )
        self.assertIn(
            Segment(
                slug="desktop_segment_3",
                friendly_name="Desktop Segment 3",
                application=NimbusExperiment.Application.DESKTOP,
                description="Firefox desktop segment used for testing",
                select_expression="",
            ),
            desktop_segments,
        )


class TestCheckSegments(TestCase):
    def setUp(self):
        Segments.clear_cache()

    def test_valid_segments_do_not_trigger_check_error(self):
        errors = check_segments(app_configs=None, segments_data=mock_get_segments())
        self.assertEqual(errors, [])

    def test_invalid_segments_trigger_check_error(self):
        errors = check_segments(
            app_configs=None, segments_data=mock_get_invalid_segments()
        )
        self.assertEqual(
            errors,
            [Error(msg="Error loading Segments: Expected SegmentDefinition, got dict")],
        )
