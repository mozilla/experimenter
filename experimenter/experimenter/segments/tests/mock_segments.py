from metric_config_parser.segment import SegmentDefinition


def mock_get_segments():
    return {
        "fenix": [
            SegmentDefinition(
                name="fenix_segment",
                data_source=None,
                select_expression="{{agg_sum('ad_click')}}",
                friendly_name="Fenix Segment",
                description="Fenix segment for testing",
            )
        ],
        "firefox_desktop": [
            SegmentDefinition(
                name="desktop_segment_1",
                data_source=None,
                select_expression="country_code in ('IN', 'US')",
                friendly_name="Desktop Segment 1",
                description="Firefox desktop segment used for testing",
            ),
            SegmentDefinition(
                name="desktop_segment_2",
                data_source=None,
                select_expression="country_code in ('IN', 'US')",
                friendly_name="Desktop Segment 2",
                description="",
            ),
            SegmentDefinition(
                name="desktop_segment_3",
                data_source=None,
                select_expression="",
                friendly_name="Desktop Segment 3",
                description="Firefox desktop segment used for testing",
            ),
        ],
    }


def mock_get_invalid_segments():
    return {"fenix": [{"test": "test_segment"}]}
