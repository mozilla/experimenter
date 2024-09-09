import json
from unittest import TestCase

import pytest
from pydantic import ValidationError

from mozilla_nimbus_schemas.jetstream import (
    SampleSizes,
    SampleSizesFactory,
)

"""
Test cases for population sizing schemas.
"""


class TestPopulationSizing(TestCase):
    maxDiff = None

    def test_parse_population_sizing(self):
        """Test against known good data."""
        sizing_test_data = """
        {
            "firefox_desktop:release:['EN-US']:US": {
                "new": {
                    "target_recipe": {
                        "app_id": "firefox_desktop",
                        "channel": "release",
                        "locale": "('EN-US')",
                        "country": "US",
                        "new_or_existing": "new"
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
                        "new_or_existing": "existing"
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
            },
            "firefox_ios:release:['EN-US']:US": {
                "new": {
                    "target_recipe": {
                        "app_id": "firefox_desktop",
                        "channel": "release",
                        "language": "('EN-US')",
                        "country": "US",
                        "new_or_existing": "new"
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
                        "language": "('EN-US')",
                        "country": "US",
                        "new_or_existing": "existing"
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
        sample_sizes = SampleSizes.model_validate_json(sizing_test_data)
        self.assertEqual(
            json.dumps(json.loads(sizing_test_data), separators=(",", ":")),
            sample_sizes.model_dump_json(exclude_unset=True),
        )

    def test_parse_population_sizing_factory(self):
        sample_sizes = SampleSizesFactory.build()
        SampleSizes.model_validate(sample_sizes)

    def test_parse_population_sizing_factory_invalid(self):
        sample_sizes_dict = SampleSizesFactory.build().model_dump()
        first_key = list(sample_sizes_dict.keys())[0]
        sample_sizes_dict[first_key]["BAD"] = {}
        with pytest.raises(ValidationError):
            SampleSizes.model_validate(sample_sizes_dict)
