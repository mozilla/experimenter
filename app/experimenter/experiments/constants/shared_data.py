# flake8: noqa
NIMBUS_DATA = {
    "Audiences": {
        "all_english": {
            "name": "All English users",
            "description": "All users in en-* locales using the release channel.",
            "targeting": "localeLanguageCode == 'en' && browserSettings.update.channel == '{firefox_channel}'",
            "desktop_telemetry": "STARTS_WITH(environment.settings.locale, 'en')",
        },
        "us_only": {
            "name": "US users (en)",
            "description": "All users in the US with an en-* locale using the release channel.",
            "targeting": "localeLanguageCode == 'en' && region == 'US' && browserSettings.update.channel == '{firefox_channel}'",
            "desktop_telemetry": "STARTS_WITH(environment.settings.locale, 'en') AND normalized_country_code = 'US'",
        },
        "first_run": {
            "name": "First start-up users (en)",
            "description": "First start-up users (e.g. for about:welcome) with an en-* locale using the release channel.",
            "targeting": "localeLanguageCode == 'en' && (isFirstStartup || '{slug}' in activeExperiments) && browserSettings.update.channel == '{firefox_channel}'",
            "desktop_telemetry": "STARTS_WITH(environment.settings.locale, 'en') AND payload.info.profile_subsession_counter = 1",
        },
    },
    "ExperimentDesignPresets": {
        "empty_aa": {
            "name": "A/A Experiment",
            "description": "A design for diagnostic testing of targeting or enrollment. Fixed to 1% of the population.",
            "preset": {
                "filter_expression": "env.version|versionCompare('{minFirefoxVersion}') >= 0",
                "targeting": '[{randomizationUnit}, "{bucketNamespace}"]|bucketSample({bucketStart}, {bucketCount}, {bucketTotal}) && {audienceTargeting}',
                "arguments": {
                    "proposedDuration": 28,
                    "proposedEnrollment": 7,
                    "branches": [
                        {"slug": "control", "ratio": 1, "value": None},
                        {"slug": "treatment", "ratio": 1, "value": None},
                    ],
                    "bucketConfig": {
                        "randomizationUnit": "userId",
                        "count": 100,
                        "total": 10000,
                    },
                },
            },
        }
    },
    "features": {
        "picture_in_picture": {
            "name": "Picture-in-Picture",
            "description": "Counts the fraction of users and the number of times that users open Picture-in-Picture\nwindows from videos. PiP can be opened by clicking on the PiP overlay or the video's context\nmenu.\n",
            "telemetry": [
                {
                    "kind": "event",
                    "event_category": "pictureinpicture",
                    "event_method": "create",
                    "event_object": "player",
                }
            ],
            "slug": "picture_in_picture",
        },
        "pinned_tabs": {
            "name": "Pinned tabs",
            "description": "Counts the number of times that a client pinned a tab. This doesn't measure whether users\nalready had tabs pinned when observation began.\n",
            "telemetry": [
                {"kind": "scalar", "name": "browser.engagement.tab_pinned_event_count"}
            ],
            "slug": "pinned_tabs",
        },
    },
}
