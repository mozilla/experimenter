/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export const MOCK_UNAVAILABLE_ANALYSIS = {
  show_analysis: true,
  daily: null,
  weekly: null,
  overall: null,
};

export const mockAnalysis = (modifications = {}) =>
  Object.assign(
    {
      other_metrics: {
        feature_d: "Feature D",
      },
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
          is_control: true,
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
            retained: {
              absolute: {
                first: {
                  point: 0.6421568627450981,
                  lower: 0.5752946065083696,
                  upper: 0.7063786618426765,
                },
                all: [
                  {
                    point: 0.6421568627450981,
                    lower: 0.5752946065083696,
                    upper: 0.7063786618426765,
                  },
                ],
              },
              difference: {
                first: {
                  point: 0.032060163779913255,
                  lower: -0.06502380421429996,
                  upper: 0.12483606976999304,
                },
                all: [
                  {
                    point: 0.032060163779913255,
                    lower: -0.06502380421429996,
                    upper: 0.12483606976999304,
                  },
                ],
              },
              relative_uplift: {
                first: {},
                all: [],
              },
              significance: "neutral",
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

/*
 * An incomplete analysis is missing one or both of `retained` and/or `search_count`
 */
export const mockIncompleteAnalysis = (modifications = {}) =>
  Object.assign(
    {
      other_metrics: {
        feature_d: "Feature D",
      },
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
          is_control: true,
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
