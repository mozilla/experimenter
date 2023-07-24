import json
from unittest import TestCase

from mozilla_nimbus_schemas.jetstream import SampleSizes

"""
Test cases for population sizing schemas.
"""


class TestPopulationSizing(TestCase):
    def test_parse_population_sizing(self):
        """Test against known good data."""
        sizing_test_data = """
        {
            "firefox_desktop:release:['EN-US']:US:108": {
                "new": {
                    "target_recipe": {
                        "app_id": "firefox_desktop",
                        "channel": "release",
                        "locale": "('EN-US')",
                        "country": "US",
                        "new_or_existing": "new",
                        "minimum_version": "108"
                    },
                    "sample_sizes": {
                        "Power0.8EffectSize0.05": {
                            "metrics": {
                                "active_hours": {
                                    "number_of_clients_targeted": 35,
                                    "sample_size_per_branch": 3.0,
                                    "population_percent_per_branch": 8.571428571
                                },
                                "search_count": {
                                    "number_of_clients_targeted": 35,
                                    "sample_size_per_branch": 5.0,
                                    "population_percent_per_branch": 14.285714285
                                },
                                "days_of_use": {
                                    "number_of_clients_targeted": 35,
                                    "sample_size_per_branch": 20.0,
                                    "population_percent_per_branch": 57.142857142
                                }
                            },
                            "parameters": {
                                "power": 0.8,
                                "effect_size": 0.05
                            }
                        }
                    }
                },
                "existing": {
                    "target_recipe": {
                        "app_id": "firefox_desktop",
                        "channel": "release",
                        "locale": "('EN-US')",
                        "country": "US",
                        "new_or_existing": "existing",
                        "minimum_version": "108"
                    },
                    "sample_sizes": {
                        "Power0.8EffectSize0.05": {
                            "metrics": {
                                "active_hours": {
                                    "number_of_clients_targeted": 10000,
                                    "sample_size_per_branch": 100000.0,
                                    "population_percent_per_branch": 1000.0
                                },
                                "tagged_search_count": {
                                    "number_of_clients_targeted": 10000,
                                    "sample_size_per_branch": 100.0,
                                    "population_percent_per_branch": 1.0
                                },
                                "days_of_use": {
                                    "number_of_clients_targeted": 10000,
                                    "sample_size_per_branch": 10000.0,
                                    "population_percent_per_branch": 100.0
                                }
                            },
                            "parameters": {
                                "power": 0.8,
                                "effect_size": 0.05
                            }
                        }
                    }
                }
            }
        }
        """
        sample_sizes = SampleSizes.parse_raw(sizing_test_data)
        self.assertEqual(json.dumps(json.loads(sizing_test_data)), sample_sizes.json())
