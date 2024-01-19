/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { SampleSizes, SizingByUserType } from "@mozilla/nimbus-schemas";

export const MOCK_UNAVAILABLE_ANALYSIS = {
  show_analysis: true,
  daily: null,
  weekly: null,
  overall: null,
  errors: null,
  metadata: {
    metrics: {},
    outcomes: {},
  },
};

export const MOCK_METADATA = {
  analysis_start_time: "2022-08-11 20:06:30.309647+00:00",
  metrics: {
    feature_b: {
      bigger_is_better: true,
      description:
        "This is a metric description. It's made by a data scientist at the creation time of the metric [I'm a link](https://www.example.com)",
      friendly_name: "Feature B",
    },
    feature_d: {
      bigger_is_better: true,
      description:
        "This is a metric description. It's made by a data scientist at the creation time of the metric [I'm a link](https://www.example.com)",
      friendly_name: "Feature D Friendly Name",
    },
    search_count: {
      bigger_is_better: true,
      description:
        "This is a metric description for search. It's made by a data scientist at the creation time of the metric [Link](https://www.example.com)",
      friendly_name: "Search Count",
    },
    picture_in_picture: {
      bigger_is_better: true,
      description:
        "This is a metric description for picture_in_picture. It's made by a data scientist at the creation time of the metric [Link](https://www.example.com)",
      friendly_name: "Picture in picture",
    },
  },
  outcomes: {
    outcome_test: {
      commit_hash: "1234abcdef",
      default_metrics: [],
      description: "Outcome for testing",
      friendly_name: "Test Outcome",
      metrics: ["picture_in_picture"],
      slug: "outcome_test",
      bigger_is_better: false,
    },
  },
};

/**
 * Certain experiment properties can be overridden in the Jetstream config which are exposed in
 * the metadata via an `external_config` object in schema version 4+. If overrides exist, they
 * don't impact an experiment beyond analysis data, and should be referenced as the "true"
 * properties used when the analysis occurs.
 *
 * `external_config` will be `undefined` prior to schema version 4. It will be `null` if no
 * overrides are present.
 */
export const MOCK_METADATA_EXTERNAL_CONFIG = {
  start_date: "2021-05-26",
  end_date: "2021-06-06",
  enrollment_period: 9,
  reference_branch: "treatment",
  skip: true,
  url: "https://github.com/mozilla/metric-hub/",
};

export const MOCK_METADATA_WITH_CONFIG = {
  ...MOCK_METADATA,
  external_config: {
    ...MOCK_METADATA_EXTERNAL_CONFIG,
  },
};

export const CONTROL_NEUTRAL = {
  absolute: {
    first: {
      point: 0.05,
      count: 10,
      lower: 0.024357271316207685,
      upper: 0.08411463700173483,
    },
    all: [
      {
        point: 0.05,
        count: 10,
        lower: 0.024357271316207685,
        upper: 0.08411463700173483,
      },
    ],
  },
  difference: {
    first: {},
    all: [],
  },
  relative_uplift: {
    first: {},
    all: [],
  },
};

export const TREATMENT_NEUTRAL = {
  absolute: {
    first: {
      point: 0.049019607843137254,
      count: 10,
      lower: 0.023872203557007872,
      upper: 0.08249069209461024,
    },
    all: [
      {
        point: 0.049019607843137254,
        count: 10,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
      },
    ],
  },
  difference: {
    first: {
      point: -0.0006569487628876534,
      upper: 0.04316381736512019,
      lower: 0.04175095963994029,
    },
    all: [
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: 0.04175095963994029,
      },
    ],
  },
  relative_uplift: {
    first: {
      lower: -0.455210299676828,
      upper: 0.5104985718410426,
      point: -0.06233954570562385,
    },
    all: [
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
      },
    ],
  },
  significance: { overall: { "1": "neutral" }, weekly: {} },
};

export const TREATMENT_NEGATIVE = Object.assign({}, TREATMENT_NEUTRAL, {
  significance: { overall: { "1": "negative" }, weekly: {} },
});

export const WEEKLY_CONTROL = {
  absolute: {
    first: {
      point: 0.05,
      lower: 0.024357271316207685,
      upper: 0.08411463700173483,
      window_index: 1,
    },
    all: [
      {
        point: 0.05,
        lower: 0.024357271316207685,
        upper: 0.08411463700173483,
        window_index: 1,
      },
      {
        point: 0.05,
        lower: 0.024357271316207685,
        upper: 0.08411463700173483,
        window_index: 2,
      },
    ],
  },
  difference: {
    first: {},
    all: [],
  },
  relative_uplift: {
    first: {},
    all: [],
  },
};

export const WONKY_WEEKLY_TREATMENT = {
  absolute: {
    first: {
      point: 0.049019607843137254,
      lower: 0.023872203557007872,
      upper: 0.08249069209461024,
      count: 10,
      window_index: 1,
    },
    all: [
      {
        point: 0.049019607843137254,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
        count: 10,
        window_index: 1,
      },
      {
        point: 0.06019607843137254,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
        count: 10,
        window_index: 5,
      },
    ],
  },
  difference: {
    first: {
      point: -0.0006569487628876534,
      upper: 0.04316381736512019,
      lower: 0.04175095963994029,
      window_index: 1,
    },
    all: [
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: -0.04175095963994029,
        window_index: 1,
      },
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: -0.04175095963994029,
        window_index: 5,
      },
    ],
  },
  relative_uplift: {
    first: {
      lower: -0.455210299676828,
      upper: 0.5104985718410426,
      point: -0.06233954570562385,
      window_index: 1,
    },
    all: [
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
        window_index: 1,
      },
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
        window_index: 5,
      },
    ],
  },
  significance: { overall: {}, weekly: { "1": "negative" } },
};

export const WEEKLY_TREATMENT = {
  absolute: {
    first: {
      point: 0.049019607843137254,
      lower: 0.023872203557007872,
      upper: 0.08249069209461024,
      count: 10,
      window_index: 1,
    },
    all: [
      {
        point: 0.049019607843137254,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
        count: 10,
        window_index: 1,
      },
      {
        point: 0.06019607843137254,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
        count: 10,
        window_index: 2,
      },
    ],
  },
  difference: {
    first: {
      point: -0.0006569487628876534,
      upper: 0.04316381736512019,
      lower: 0.04175095963994029,
      window_index: 1,
    },
    all: [
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: -0.04175095963994029,
        window_index: 1,
      },
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: -0.04175095963994029,
        window_index: 2,
      },
    ],
  },
  relative_uplift: {
    first: {
      lower: -0.455210299676828,
      upper: 0.5104985718410426,
      point: -0.06233954570562385,
      window_index: 1,
    },
    all: [
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
        window_index: 1,
      },
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
        window_index: 2,
      },
    ],
  },
  significance: { overall: {}, weekly: { "1": "negative" } },
};

export const WEEKLY_IDENTITY = {
  absolute: {
    all: [
      {
        point: 198,
      },
      {
        point: 198,
      },
    ],
    first: {
      point: 198,
    },
  },
  difference: {
    first: {},
    all: [],
  },
  relative_uplift: {
    first: {},
    all: [],
  },
  percent: 50,
};

export const WEEKLY_EXTRA_LONG = {
  absolute: {
    first: {
      point: 0.049019607843137254,
      lower: 0.023872203557007872,
      upper: 0.08249069209461024,
      count: 10,
      window_index: 1,
    },
    all: [
      {
        point: 0.049019607843137254,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
        count: 10,
        window_index: 1,
      },
      {
        point: 0.06019607843137254,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
        count: 10,
        window_index: 5,
      },
      {
        point: 0.07019607843137254,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
        count: 10,
        window_index: 10,
      },
      {
        point: 0.08019607843137254,
        lower: 0.023872203557007872,
        upper: 0.08249069209461024,
        count: 10,
        window_index: 15,
      },
    ],
  },
  difference: {
    first: {
      point: -0.0006569487628876534,
      upper: 0.04316381736512019,
      lower: 0.04175095963994029,
      window_index: 1,
    },
    all: [
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: -0.04175095963994029,
        window_index: 1,
      },
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: -0.04175095963994029,
        window_index: 5,
      },
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: -0.04175095963994029,
        window_index: 10,
      },
      {
        point: -0.0006569487628876534,
        upper: 0.04316381736512019,
        lower: -0.04175095963994029,
        window_index: 15,
      },
    ],
  },
  relative_uplift: {
    first: {
      lower: -0.455210299676828,
      upper: 0.5104985718410426,
      point: -0.06233954570562385,
      window_index: 1,
    },
    all: [
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
        window_index: 1,
      },
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
        window_index: 5,
      },
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
        window_index: 10,
      },
      {
        lower: -0.455210299676828,
        upper: 0.5104985718410426,
        point: -0.06233954570562385,
        window_index: 15,
      },
    ],
  },
  significance: { overall: {}, weekly: { "1": "negative" } },
};

export const MOCK_SIZING_DATA: SizingByUserType = {
  new: {
    target_recipe: {
      app_id: "firefox_desktop",
      channel: "release",
      locale: "('EN-US')",
      country: "US",
      new_or_existing: "new",
    },
    sample_sizes: {
      "Power0.8EffectSize0.05": {
        metrics: {
          active_hours: {
            number_of_clients_targeted: 10000,
            sample_size_per_branch: 1233.0,
            population_percent_per_branch: 18.571428571,
          },
          search_count: {
            number_of_clients_targeted: 10000,
            sample_size_per_branch: 1235.0,
            population_percent_per_branch: 114.285714285,
          },
          days_of_use: {
            number_of_clients_targeted: 10000,
            sample_size_per_branch: 12320.0,
            population_percent_per_branch: 157.142857142,
          },
        },
        parameters: {
          power: 0.8,
          effect_size: 0.05,
        },
      },
      "Power0.8EffectSize0.01": {
        metrics: {
          active_hours: {
            number_of_clients_targeted: 10000,
            sample_size_per_branch: 1233.0,
            population_percent_per_branch: 18.571428571,
          },
          search_count: {
            number_of_clients_targeted: 10000,
            sample_size_per_branch: 1235.0,
            population_percent_per_branch: 114.285714285,
          },
          days_of_use: {
            number_of_clients_targeted: 10000,
            sample_size_per_branch: 12320.0,
            population_percent_per_branch: 157.142857142,
          },
        },
        parameters: {
          power: 0.8,
          effect_size: 0.01,
        },
      },
    },
  },
  existing: {
    target_recipe: {
      app_id: "firefox_desktop",
      channel: "release",
      locale: "('EN-US')",
      country: "US",
      new_or_existing: "existing",
    },
    sample_sizes: {
      "Power0.8EffectSize0.05": {
        metrics: {
          active_hours: {
            number_of_clients_targeted: 100000,
            sample_size_per_branch: 12343.0,
            population_percent_per_branch: 8.571428571,
          },
          search_count: {
            number_of_clients_targeted: 100000,
            sample_size_per_branch: 12345.0,
            population_percent_per_branch: 14.285714285,
          },
          days_of_use: {
            number_of_clients_targeted: 100000,
            sample_size_per_branch: 123420.0,
            population_percent_per_branch: 57.142857142,
          },
        },
        parameters: {
          power: 0.8,
          effect_size: 0.05,
        },
      },
      "Power0.8EffectSize0.01": {
        metrics: {
          active_hours: {
            number_of_clients_targeted: 100000,
            sample_size_per_branch: 12343.0,
            population_percent_per_branch: 8.571428571,
          },
          search_count: {
            number_of_clients_targeted: 100000,
            sample_size_per_branch: 12345.0,
            population_percent_per_branch: 14.285714285,
          },
          days_of_use: {
            number_of_clients_targeted: 100000,
            sample_size_per_branch: 123420.0,
            population_percent_per_branch: 57.142857142,
          },
        },
        parameters: {
          power: 0.8,
          effect_size: 0.01,
        },
      },
    },
  },
};

export const MOCK_SIZING: SampleSizes = {
  "firefox_desktop:release:['EN-US']:US": MOCK_SIZING_DATA,
  "firefox_desktop:nightly:['EN-US']:US": MOCK_SIZING_DATA,
  "firefox_desktop:release:['EN-CA','EN-US']:['CA','US']": MOCK_SIZING_DATA,
  "firefox_ios:release:['EN-CA','EN-US']:['CA','US']": MOCK_SIZING_DATA,
};

export const weeklyMockAnalysis = (modifications = {}) =>
  Object.assign(
    {
      control: {
        is_control: true,
        branch_data: {
          search_metrics: {
            search_count: WEEKLY_CONTROL,
          },
          other_metrics: {
            identity: WEEKLY_IDENTITY,
            feature_d: WEEKLY_CONTROL,
            retained: WEEKLY_CONTROL,
            days_of_use: WEEKLY_CONTROL,
          },
        },
      },
      treatment: {
        is_control: false,
        branch_data: {
          search_metrics: {
            search_count: WEEKLY_TREATMENT,
          },
          other_metrics: {
            identity: WEEKLY_IDENTITY,
            feature_d: WEEKLY_TREATMENT,
            retained: WEEKLY_TREATMENT,
            days_of_use: WEEKLY_TREATMENT,
          },
        },
      },
    },
    modifications,
  );

export const mockAnalysis = (modifications = {}) =>
  Object.assign(
    {
      other_metrics: { other_metrics: { feature_d: "Feature D" } },
      metadata: MOCK_METADATA,
      show_analysis: true,
      errors: {
        experiment: [
          {
            exception:
              "(<class 'jetstream.errors.NoEnrollmentPeriodException'>, NoEnrollmentPeriodException('demo-slug -> Experiment has no enrollment period'), <traceback object at 0x7f50b65ce200>)",
            exception_type: "NoEnrollmentPeriodException",
            experiment: "demo-slug",
            filename: "cli.py",
            func_name: "execute",
            log_level: "ERROR",
            message: "demo-slug -> Experiment has no enrollment period",
            metric: null,
            statistic: null,
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
        ],
        picture_in_picture: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric picture_in_picture: 'data' contains null values'), None)",
            exception_type: "StatisticComputationException",
            experiment: "demo-slug",
            filename: "statistics.py",
            func_name: "apply",
            log_level: "ERROR",
            message:
              "Error while computing statistic bootstrap_mean for metric picture_in_picture: 'data' contains null values",
            metric: "picture_in_picture",
            statistic: "bootstrap_mean",
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
        ],
        feature_b: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values'), None)",
            exception_type: "StatisticComputationException",
            experiment: "demo-slug",
            filename: "statistics.py",
            func_name: "apply",
            log_level: "ERROR",
            message:
              "Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values",
            metric: "feature_b",
            statistic: "bootstrap_mean",
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
        ],
      },
      daily: { enrollments: { all: [] } },
      weekly: { enrollments: { all: weeklyMockAnalysis() } },
      overall: {
        enrollments: {
          all: {
            control: {
              is_control: true,
              branch_data: {
                other_metrics: {
                  identity: {
                    absolute: {
                      all: [
                        {
                          point: 198,
                        },
                      ],
                      first: {
                        point: 198,
                      },
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                    percent: 45,
                  },
                  retained: {
                    absolute: {
                      all: [
                        {
                          point: 0.9261083743842364,
                          lower: 0.8864481497569532,
                          upper: 0.9578449264993547,
                        },
                      ],
                      first: {
                        point: 14.967359019193298,
                        lower: 10.534758870048162,
                        upper: 20.754349791764547,
                      },
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  picture_in_picture_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  picture_in_picture: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_b_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_b: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_c_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_c: CONTROL_NEUTRAL,
                  feature_d: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  outcome_d: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  days_of_use: CONTROL_NEUTRAL,
                  qualified_cumulative_days_of_use: CONTROL_NEUTRAL,
                },
                search_metrics: {
                  search_count: {
                    absolute: {
                      all: [
                        {
                          point: 14.967359019193298,
                          lower: 10.534758870048162,
                          upper: 20.754349791764547,
                        },
                      ],
                      first: {
                        point: 14.967359019193298,
                        lower: 10.534758870048162,
                        upper: 20.754349791764547,
                      },
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                },
              },
            },
            treatment: {
              is_control: false,
              branch_data: {
                other_metrics: {
                  identity: {
                    absolute: {
                      first: {
                        point: 200,
                      },
                      all: [
                        {
                          point: 200,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                    percent: 55,
                  },
                  retained: TREATMENT_NEUTRAL,
                  picture_in_picture_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  picture_in_picture: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  feature_b_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "negative" }, weekly: {} },
                  },
                  feature_b: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "negative" }, weekly: {} },
                  },
                  feature_c_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "neutral" }, weekly: {} },
                  },
                  feature_c: TREATMENT_NEUTRAL,
                  days_of_use: TREATMENT_NEUTRAL,
                  qualified_cumulative_days_of_use: TREATMENT_NEUTRAL,
                  feature_d: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  outcome_d: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                },
                search_metrics: {
                  search_count: TREATMENT_NEGATIVE,
                },
              },
            },
          },
        },
      },
    },
    modifications,
  );

export const mockAnalysisWithSegments = mockAnalysis({
  overall: {
    enrollments: {
      all: {
        control: {
          is_control: true,
          branch_data: {
            other_metrics: {
              identity: {
                absolute: {
                  all: [
                    {
                      point: 198,
                    },
                  ],
                  first: {
                    point: 198,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
                percent: 45,
              },
              retained: {
                absolute: {
                  all: [
                    {
                      point: 0.9261083743842364,
                      lower: 0.8864481497569532,
                      upper: 0.9578449264993547,
                    },
                  ],
                  first: {
                    point: 14.967359019193298,
                    lower: 10.534758870048162,
                    upper: 20.754349791764547,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              picture_in_picture_ever_used: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              picture_in_picture: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_b_ever_used: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_b: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_c_ever_used: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_c: CONTROL_NEUTRAL,
              feature_d: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              outcome_d: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              days_of_use: CONTROL_NEUTRAL,
              qualified_cumulative_days_of_use: CONTROL_NEUTRAL,
            },
            search_metrics: {
              search_count: {
                absolute: {
                  all: [
                    {
                      point: 14.967359019193298,
                      lower: 10.534758870048162,
                      upper: 20.754349791764547,
                    },
                  ],
                  first: {
                    point: 14.967359019193298,
                    lower: 10.534758870048162,
                    upper: 20.754349791764547,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
            },
          },
        },
        treatment: {
          is_control: false,
          branch_data: {
            other_metrics: {
              identity: {
                absolute: {
                  first: {
                    point: 200,
                  },
                  all: [
                    {
                      point: 200,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
                percent: 55,
              },
              retained: TREATMENT_NEUTRAL,
              picture_in_picture_ever_used: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              picture_in_picture: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              feature_b_ever_used: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "negative" }, weekly: {} },
              },
              feature_b: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "negative" }, weekly: {} },
              },
              feature_c_ever_used: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "neutral" }, weekly: {} },
              },
              feature_c: TREATMENT_NEUTRAL,
              days_of_use: TREATMENT_NEUTRAL,
              qualified_cumulative_days_of_use: TREATMENT_NEUTRAL,
              feature_d: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              outcome_d: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
            },
            search_metrics: {
              search_count: TREATMENT_NEGATIVE,
            },
          },
        },
      },
      a_different_segment: {
        control: {
          is_control: true,
          branch_data: {
            other_metrics: {
              identity: {
                absolute: {
                  all: [
                    {
                      point: 90,
                    },
                  ],
                  first: {
                    point: 90,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
                percent: 45,
              },
              retained: {
                absolute: {
                  all: [
                    {
                      point: 0.9361083743842364,
                      lower: 0.8874481497569532,
                      upper: 0.9778449264993547,
                    },
                  ],
                  first: {
                    point: 13.967359019193298,
                    lower: 9.534758870048162,
                    upper: 19.754349791764547,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              picture_in_picture_ever_used: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              picture_in_picture: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_b_ever_used: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_b: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_c_ever_used: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_c: CONTROL_NEUTRAL,
              feature_d: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              outcome_d: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              days_of_use: CONTROL_NEUTRAL,
              qualified_cumulative_days_of_use: CONTROL_NEUTRAL,
            },
            search_metrics: {
              search_count: {
                absolute: {
                  all: [
                    {
                      point: 13.967359019193298,
                      lower: 9.534758870048162,
                      upper: 19.754349791764547,
                    },
                  ],
                  first: {
                    point: 13.967359019193298,
                    lower: 9.534758870048162,
                    upper: 19.754349791764547,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
            },
          },
        },
        treatment: {
          is_control: false,
          branch_data: {
            other_metrics: {
              identity: {
                absolute: {
                  first: {
                    point: 200,
                  },
                  all: [
                    {
                      point: 200,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
                percent: 55,
              },
              retained: TREATMENT_NEUTRAL,
              picture_in_picture_ever_used: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              picture_in_picture: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              feature_b_ever_used: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "negative" }, weekly: {} },
              },
              feature_b: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "negative" }, weekly: {} },
              },
              feature_c_ever_used: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "neutral" }, weekly: {} },
              },
              feature_c: TREATMENT_NEUTRAL,
              days_of_use: TREATMENT_NEUTRAL,
              qualified_cumulative_days_of_use: TREATMENT_NEUTRAL,
              feature_d: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              outcome_d: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
            },
            search_metrics: {
              search_count: TREATMENT_NEGATIVE,
            },
          },
        },
      },
    },
  },
});

export const mockAnalysisWithExposures = mockAnalysis({
  overall: {
    enrollments: {
      all: {
        control: {
          is_control: true,
          branch_data: {
            other_metrics: {
              identity: {
                absolute: {
                  all: [
                    {
                      point: 198,
                    },
                  ],
                  first: {
                    point: 198,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
                percent: 45,
              },
              retained: {
                absolute: {
                  all: [
                    {
                      point: 0.9261083743842364,
                      lower: 0.8864481497569532,
                      upper: 0.9578449264993547,
                    },
                  ],
                  first: {
                    point: 14.967359019193298,
                    lower: 10.534758870048162,
                    upper: 20.754349791764547,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              picture_in_picture_ever_used: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              picture_in_picture: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_b_ever_used: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_b: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_c_ever_used: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_c: CONTROL_NEUTRAL,
              feature_d: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              outcome_d: {
                absolute: {
                  first: {
                    point: 0.05,
                    count: 10,
                    lower: 0.024357271316207685,
                    upper: 0.08411463700173483,
                  },
                  all: [
                    {
                      point: 0.05,
                      count: 10,
                      lower: 0.024357271316207685,
                      upper: 0.08411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              days_of_use: CONTROL_NEUTRAL,
              qualified_cumulative_days_of_use: CONTROL_NEUTRAL,
            },
            search_metrics: {
              search_count: {
                absolute: {
                  all: [
                    {
                      point: 14.967359019193298,
                      lower: 10.534758870048162,
                      upper: 20.754349791764547,
                    },
                  ],
                  first: {
                    point: 14.967359019193298,
                    lower: 10.534758870048162,
                    upper: 20.754349791764547,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
            },
          },
        },
        treatment: {
          is_control: false,
          branch_data: {
            other_metrics: {
              identity: {
                absolute: {
                  first: {
                    point: 200,
                  },
                  all: [
                    {
                      point: 200,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
                percent: 55,
              },
              retained: TREATMENT_NEUTRAL,
              picture_in_picture_ever_used: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              picture_in_picture: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              feature_b_ever_used: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "negative" }, weekly: {} },
              },
              feature_b: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "negative" }, weekly: {} },
              },
              feature_c_ever_used: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "neutral" }, weekly: {} },
              },
              feature_c: TREATMENT_NEUTRAL,
              days_of_use: TREATMENT_NEUTRAL,
              qualified_cumulative_days_of_use: TREATMENT_NEUTRAL,
              feature_d: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              outcome_d: {
                absolute: {
                  first: {
                    point: 0.049019607843137254,
                    count: 10,
                    lower: 0.023872203557007872,
                    upper: 0.08249069209461024,
                  },
                  all: [
                    {
                      point: 0.049019607843137254,
                      count: 10,
                      lower: 0.023872203557007872,
                      upper: 0.08249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0006569487628876534,
                    upper: 0.04316381736512019,
                    lower: 0.04175095963994029,
                  },
                  all: [
                    {
                      point: -0.0006569487628876534,
                      upper: 0.04316381736512019,
                      lower: 0.04175095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.455210299676828,
                    upper: 0.5104985718410426,
                    point: -0.06233954570562385,
                  },
                  all: [
                    {
                      lower: -0.455210299676828,
                      upper: 0.5104985718410426,
                      point: -0.06233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
            },
            search_metrics: {
              search_count: TREATMENT_NEGATIVE,
            },
          },
        },
      },
    },
    exposures: {
      all: {
        control: {
          is_control: true,
          branch_data: {
            other_metrics: {
              identity: {
                absolute: {
                  all: [
                    {
                      point: 90,
                    },
                  ],
                  first: {
                    point: 90,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
                percent: 45,
              },
              retained: {
                absolute: {
                  all: [
                    {
                      point: 0.9361083743842364,
                      lower: 0.8874481497569532,
                      upper: 0.9778449264993547,
                    },
                  ],
                  first: {
                    point: 13.967359019193298,
                    lower: 9.534758870048162,
                    upper: 19.754349791764547,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              picture_in_picture_ever_used: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              picture_in_picture: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_b_ever_used: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_b: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_c_ever_used: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              feature_c: CONTROL_NEUTRAL,
              feature_d: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              outcome_d: {
                absolute: {
                  first: {
                    point: 0.06,
                    count: 4,
                    lower: 0.034357271316207685,
                    upper: 0.09411463700173483,
                  },
                  all: [
                    {
                      point: 0.06,
                      count: 4,
                      lower: 0.034357271316207685,
                      upper: 0.09411463700173483,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
              days_of_use: CONTROL_NEUTRAL,
              qualified_cumulative_days_of_use: CONTROL_NEUTRAL,
            },
            search_metrics: {
              search_count: {
                absolute: {
                  all: [
                    {
                      point: 13.967359019193298,
                      lower: 9.534758870048162,
                      upper: 19.754349791764547,
                    },
                  ],
                  first: {
                    point: 13.967359019193298,
                    lower: 9.534758870048162,
                    upper: 19.754349791764547,
                  },
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
              },
            },
          },
        },
        treatment: {
          is_control: false,
          branch_data: {
            other_metrics: {
              identity: {
                absolute: {
                  first: {
                    point: 200,
                  },
                  all: [
                    {
                      point: 200,
                    },
                  ],
                },
                difference: {
                  first: {},
                  all: [],
                },
                relative_uplift: {
                  first: {},
                  all: [],
                },
                percent: 55,
              },
              retained: TREATMENT_NEUTRAL,
              picture_in_picture_ever_used: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              picture_in_picture: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              feature_b_ever_used: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "negative" }, weekly: {} },
              },
              feature_b: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "negative" }, weekly: {} },
              },
              feature_c_ever_used: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "neutral" }, weekly: {} },
              },
              feature_c: TREATMENT_NEUTRAL,
              days_of_use: TREATMENT_NEUTRAL,
              qualified_cumulative_days_of_use: TREATMENT_NEUTRAL,
              feature_d: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
              outcome_d: {
                absolute: {
                  first: {
                    point: 0.059019607843137254,
                    count: 4,
                    lower: 0.033872203557007872,
                    upper: 0.09249069209461024,
                  },
                  all: [
                    {
                      point: 0.059019607843137254,
                      count: 4,
                      lower: 0.033872203557007872,
                      upper: 0.09249069209461024,
                    },
                  ],
                },
                difference: {
                  first: {
                    point: -0.0007569487628876534,
                    upper: 0.04416381736512019,
                    lower: 0.04075095963994029,
                  },
                  all: [
                    {
                      point: -0.0007569487628876534,
                      upper: 0.04416381736512019,
                      lower: 0.04075095963994029,
                    },
                  ],
                },
                relative_uplift: {
                  first: {
                    lower: -0.465210299676828,
                    upper: 0.5204985718410426,
                    point: -0.07233954570562385,
                  },
                  all: [
                    {
                      lower: -0.465210299676828,
                      upper: 0.5204985718410426,
                      point: -0.07233954570562385,
                    },
                  ],
                },
                significance: { overall: { "1": "positive" }, weekly: {} },
              },
            },
            search_metrics: {
              search_count: TREATMENT_NEGATIVE,
            },
          },
        },
      },
    },
  },
});

export const mockAnalysisWithWeeklyExposures = mockAnalysis({
  weekly: {
    enrollments: { all: weeklyMockAnalysis() },
    exposures: { all: weeklyMockAnalysis() },
  },
  overall: {},
});
/*
 * An incomplete analysis is missing one or both of `retained` and/or `search_count`
 */
export const mockIncompleteAnalysis = (modifications = {}) =>
  Object.assign(
    {
      other_metrics: { other_metrics: { feature_d: "Feature D" } },
      metadata: MOCK_METADATA,
      show_analysis: true,
      errors: { experiment: [] },
      daily: { enrollments: { all: [] } },
      weekly: { enrollments: { all: {} } },
      overall: {
        enrollments: {
          all: {
            control: {
              is_control: true,
              branch_data: {
                other_metrics: {
                  identity: {
                    absolute: {
                      all: [
                        {
                          point: 198,
                        },
                      ],
                      first: {
                        point: 198,
                      },
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                    percent: 45,
                  },
                  picture_in_picture_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  picture_in_picture: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_b_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_b: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_c_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_c: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_d: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  outcome_d: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                },
                search_metrics: {
                  search_count: {
                    absolute: {
                      all: [
                        {
                          point: 14.967359019193298,
                          lower: 10.534758870048162,
                          upper: 20.754349791764547,
                        },
                      ],
                      first: {
                        point: 14.967359019193298,
                        lower: 10.534758870048162,
                        upper: 20.754349791764547,
                      },
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                },
              },
            },
            treatment: {
              is_control: false,
              branch_data: {
                other_metrics: {
                  identity: {
                    absolute: {
                      first: {
                        point: 200,
                      },
                      all: [
                        {
                          point: 200,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                    percent: 55,
                  },
                  picture_in_picture_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  picture_in_picture: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  feature_b_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "negative" }, weekly: {} },
                  },
                  feature_b: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "negative" }, weekly: {} },
                  },
                  feature_c_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "neutral" }, weekly: {} },
                  },
                  feature_c: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "neutral" }, weekly: {} },
                  },
                  feature_d: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  outcome_d: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                },
                search_metrics: {
                  search_count: {
                    absolute: {
                      first: {
                        point: 25.456361412643364,
                        lower: 18.998951440573688,
                        upper: 33.54929175463715,
                      },
                      all: [
                        {
                          point: 25.456361412643364,
                          lower: 18.998951440573688,
                          upper: 33.54929175463715,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: 5.075852767646001,
                        upper: -5.63685604594333,
                        lower: -15.289651027022447,
                      },
                      all: [
                        {
                          point: 5.075852767646001,
                          upper: -5.63685604594333,
                          lower: -15.289651027022447,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                    significance: { overall: { "1": "negative" }, weekly: {} },
                  },
                },
              },
            },
          },
        },
      },
    },
    modifications,
  );

export const mockAnalysisWithErrors = (modifications = {}) =>
  Object.assign(
    {
      other_metrics: { other_metrics: { feature_d: "Feature D" } },
      metadata: MOCK_METADATA,
      show_analysis: true,
      errors: {
        experiment: [
          {
            exception:
              "(<class 'jetstream.errors.NoEnrollmentPeriodException'>, NoEnrollmentPeriodException('demo-slug -> Experiment has no enrollment period'), <traceback object at 0x7f50b65ce200>)",
            exception_type: "NoEnrollmentPeriodException",
            experiment: "demo-slug",
            filename: "cli.py",
            func_name: "execute",
            log_level: "ERROR",
            message: "demo-slug -> Experiment has no enrollment period",
            metric: null,
            statistic: null,
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
        ],
        picture_in_picture: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric picture_in_picture: 'data' contains null values'), None)",
            exception_type: "StatisticComputationException",
            experiment: "demo-slug",
            filename: "statistics.py",
            func_name: "apply",
            log_level: "ERROR",
            message:
              "Error while computing statistic bootstrap_mean for metric picture_in_picture: 'data' contains null values",
            metric: "picture_in_picture",
            statistic: "bootstrap_mean",
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
        ],
        feature_b: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values'), None)",
            exception_type: "StatisticComputationException",
            experiment: "demo-slug",
            filename: "statistics.py",
            func_name: "apply",
            log_level: "ERROR",
            message:
              "Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values",
            metric: "feature_b",
            statistic: "bootstrap_mean",
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values'), None)",
            exception_type: "StatisticComputationException",
            experiment: "demo-slug",
            filename: "statistics.py",
            func_name: "apply",
            log_level: "ERROR",
            message:
              "Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values",
            metric: "feature_b",
            statistic: "bootstrap_mean",
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "exposures",
            segment: "all",
          },
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values'), None)",
            exception_type: "StatisticComputationException",
            experiment: "demo-slug",
            filename: "statistics.py",
            func_name: "apply",
            log_level: "ERROR",
            message:
              "Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values",
            metric: "feature_b",
            statistic: "bootstrap_mean",
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "other_segment",
          },
        ],
      },
      daily: { enrollments: { all: [] } },
      weekly: { enrollments: { all: weeklyMockAnalysis() } },
      overall: null,
    },
    modifications,
  );

export const mockAnalysisWithErrorsAndResults = (modifications = {}) =>
  Object.assign(
    {
      other_metrics: { other_metrics: { feature_d: "Feature D" } },
      metadata: MOCK_METADATA,
      show_analysis: true,
      errors: {
        experiment: [
          {
            exception:
              "(<class 'jetstream.errors.NoEnrollmentPeriodException'>, NoEnrollmentPeriodException('demo-slug -> Experiment has no enrollment period'), <traceback object at 0x7f50b65ce200>)",
            exception_type: "NoEnrollmentPeriodException",
            experiment: "demo-slug",
            filename: "cli.py",
            func_name: "execute",
            log_level: "ERROR",
            message: "demo-slug -> Experiment has no enrollment period",
            metric: null,
            statistic: null,
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
        ],
        picture_in_picture: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric picture_in_picture: 'data' contains null values'), None)",
            exception_type: "StatisticComputationException",
            experiment: "demo-slug",
            filename: "statistics.py",
            func_name: "apply",
            log_level: "ERROR",
            message:
              "Error while computing statistic bootstrap_mean for metric picture_in_picture: 'data' contains null values",
            metric: "picture_in_picture",
            statistic: "bootstrap_mean",
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
        ],
        feature_b: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values'), None)",
            exception_type: "StatisticComputationException",
            experiment: "demo-slug",
            filename: "statistics.py",
            func_name: "apply",
            log_level: "ERROR",
            message:
              "Error while computing statistic bootstrap_mean for metric feature_b: 'data' contains null values",
            metric: "feature_b",
            statistic: "bootstrap_mean",
            timestamp: "2022-08-11 20:06:35+00:00",
            analysis_basis: "enrollments",
            segment: "all",
          },
        ],
      },
      daily: { enrollments: { all: [] } },
      weekly: { enrollments: { all: weeklyMockAnalysis() } },
      overall: {
        enrollments: {
          all: {
            control: {
              is_control: true,
              branch_data: {
                other_metrics: {
                  identity: {
                    absolute: {
                      all: [
                        {
                          point: 198,
                        },
                      ],
                      first: {
                        point: 198,
                      },
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                    percent: 45,
                  },
                  retained: {
                    absolute: {
                      all: [
                        {
                          point: 0.9261083743842364,
                          lower: 0.8864481497569532,
                          upper: 0.9578449264993547,
                        },
                      ],
                      first: {
                        point: 14.967359019193298,
                        lower: 10.534758870048162,
                        upper: 20.754349791764547,
                      },
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  picture_in_picture_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_b_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_b: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_c_ever_used: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  feature_c: CONTROL_NEUTRAL,
                  feature_d: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  outcome_d: {
                    absolute: {
                      first: {
                        point: 0.05,
                        count: 10,
                        lower: 0.024357271316207685,
                        upper: 0.08411463700173483,
                      },
                      all: [
                        {
                          point: 0.05,
                          count: 10,
                          lower: 0.024357271316207685,
                          upper: 0.08411463700173483,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                  days_of_use: CONTROL_NEUTRAL,
                  qualified_cumulative_days_of_use: CONTROL_NEUTRAL,
                },
                search_metrics: {
                  search_count: {
                    absolute: {
                      all: [
                        {
                          point: 14.967359019193298,
                          lower: 10.534758870048162,
                          upper: 20.754349791764547,
                        },
                      ],
                      first: {
                        point: 14.967359019193298,
                        lower: 10.534758870048162,
                        upper: 20.754349791764547,
                      },
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                  },
                },
              },
            },
            treatment: {
              is_control: false,
              branch_data: {
                other_metrics: {
                  identity: {
                    absolute: {
                      first: {
                        point: 200,
                      },
                      all: [
                        {
                          point: 200,
                        },
                      ],
                    },
                    difference: {
                      first: {},
                      all: [],
                    },
                    relative_uplift: {
                      first: {},
                      all: [],
                    },
                    percent: 55,
                  },
                  retained: TREATMENT_NEUTRAL,
                  picture_in_picture_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  picture_in_picture: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  feature_b_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "negative" }, weekly: {} },
                  },
                  feature_b: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "negative" }, weekly: {} },
                  },
                  feature_c_ever_used: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "neutral" }, weekly: {} },
                  },
                  feature_c: TREATMENT_NEUTRAL,
                  days_of_use: TREATMENT_NEUTRAL,
                  qualified_cumulative_days_of_use: TREATMENT_NEUTRAL,
                  feature_d: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                  outcome_d: {
                    absolute: {
                      first: {
                        point: 0.049019607843137254,
                        count: 10,
                        lower: 0.023872203557007872,
                        upper: 0.08249069209461024,
                      },
                      all: [
                        {
                          point: 0.049019607843137254,
                          count: 10,
                          lower: 0.023872203557007872,
                          upper: 0.08249069209461024,
                        },
                      ],
                    },
                    difference: {
                      first: {
                        point: -0.0006569487628876534,
                        upper: 0.04316381736512019,
                        lower: 0.04175095963994029,
                      },
                      all: [
                        {
                          point: -0.0006569487628876534,
                          upper: 0.04316381736512019,
                          lower: 0.04175095963994029,
                        },
                      ],
                    },
                    relative_uplift: {
                      first: {
                        lower: -0.455210299676828,
                        upper: 0.5104985718410426,
                        point: -0.06233954570562385,
                      },
                      all: [
                        {
                          lower: -0.455210299676828,
                          upper: 0.5104985718410426,
                          point: -0.06233954570562385,
                        },
                      ],
                    },
                    significance: { overall: { "1": "positive" }, weekly: {} },
                  },
                },
                search_metrics: {
                  search_count: TREATMENT_NEGATIVE,
                },
              },
            },
          },
        },
      },
    },
    modifications,
  );
