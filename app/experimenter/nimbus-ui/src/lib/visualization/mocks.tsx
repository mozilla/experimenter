/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export const MOCK_UNAVAILABLE_ANALYSIS = {
  show_analysis: true,
  daily: null,
  weekly: null,
  overall: null,
  metadata: {
    metrics: {},
    probesets: {},
  },
};

export const MOCK_METADATA = {
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
  },
  probesets: {},
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
  significance: "neutral",
};

export const TREATMENT_NEGATIVE = Object.assign({}, TREATMENT_NEUTRAL, {
  significance: "negative",
});

export const weeklyMockAnalysis = (modifications = {}) =>
  Object.assign(
    {
      control: {
        is_control: true,
        branch_data: {
          feature_d: {
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
          },
        },
      },
      treatment: {
        is_control: false,
        branch_data: {
          feature_d: {
            absolute: {
              first: {
                point: 0.049019607843137254,
                lower: 0.023872203557007872,
                upper: 0.08249069209461024,
                window_index: 1,
              },
              all: [
                {
                  point: 0.049019607843137254,
                  lower: 0.023872203557007872,
                  upper: 0.08249069209461024,
                  window_index: 1,
                },
                {
                  point: 0.06019607843137254,
                  lower: 0.023872203557007872,
                  upper: 0.08249069209461024,
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
          },
        },
      },
    },
    modifications,
  );

export const mockAnalysis = (modifications = {}) =>
  Object.assign(
    {
      other_metrics: { feature_d: "Feature D" },
      metadata: MOCK_METADATA,
      show_analysis: true,
      daily: [],
      weekly: weeklyMockAnalysis(),
      overall: {
        control: {
          is_control: true,
          branch_data: {
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
            days_of_use: CONTROL_NEUTRAL,
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
            probeset_d: {
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
        },
        treatment: {
          is_control: false,
          branch_data: {
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
            search_count: TREATMENT_NEGATIVE,
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
              significance: "positive",
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
              significance: "positive",
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
              significance: "negative",
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
              significance: "negative",
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
              significance: "neutral",
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
              significance: "positive",
            },
            probeset_d: {
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
              significance: "positive",
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
      other_metrics: { feature_d: "Feature D" },
      metadata: MOCK_METADATA,
      show_analysis: true,
      daily: [],
      weekly: {},
      overall: {
        control: {
          is_control: true,
          branch_data: {
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
            probeset_d: {
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
        },
        treatment: {
          is_control: false,
          branch_data: {
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
              significance: "negative",
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
              significance: "positive",
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
              significance: "positive",
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
              significance: "negative",
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
              significance: "negative",
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
              significance: "neutral",
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
              significance: "neutral",
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
              significance: "positive",
            },
            probeset_d: {
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
              significance: "positive",
            },
          },
        },
      },
    },
    modifications,
  );
