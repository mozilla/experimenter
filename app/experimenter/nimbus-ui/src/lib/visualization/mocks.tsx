/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

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
  url: "https://github.com/mozilla/jetstream-config/",
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
          },
        ],
        picture_in_picture: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric search_count: 'data' contains null values'), None)",
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
          },
        ],
        feature_b: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric search_count: 'data' contains null values'), None)",
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
          },
        ],
      },
      daily: [],
      weekly: weeklyMockAnalysis(),
      overall: {
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
    modifications,
  );

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
      daily: [],
      weekly: {},
      overall: {
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
          },
        ],
        picture_in_picture: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric search_count: 'data' contains null values'), None)",
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
          },
        ],
        feature_b: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric search_count: 'data' contains null values'), None)",
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
          },
        ],
      },
      daily: [],
      weekly: weeklyMockAnalysis(),
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
          },
        ],
        picture_in_picture: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric search_count: 'data' contains null values'), None)",
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
          },
        ],
        feature_b: [
          {
            exception:
              "(<class 'jetstream.errors.StatisticComputationException'>, StatisticComputationException('Error while computing statistic bootstrap_mean for metric search_count: 'data' contains null values'), None)",
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
          },
        ],
      },
      daily: [],
      weekly: weeklyMockAnalysis(),
      overall: {
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
    modifications,
  );
