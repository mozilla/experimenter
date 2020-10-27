import { SIGNIFICANCE } from "experimenter-rapid/components/visualization/constants/analysis";
import {
  ExperimentStatus,
  FirefoxChannel,
} from "experimenter-rapid/types/experiment";
import { ExperimentData } from "experimenter-types/experiment";

export const EXPERIMENT_DATA: ExperimentData = {
  status: ExperimentStatus.LIVE,
  slug: "test-slug",
  name: "Test Name",
  objectives: "Test objectives",
  owner: "test@owner.com",
  features: ["picture_in_picture"],
  audience: "us_only",
  firefox_channel: FirefoxChannel.RELEASE,
  firefox_min_version: "78.0",
  analysis: {
    show_analysis: true,
    daily: [],
    weekly: [],
    overall: {
      control: {
        is_control: true,
        branch_data: {
          identity: {
            absolute: {
              point: 198,
            },
            difference: {},
            relative_uplift: {},
            percent: 45,
          },
          search_count: {
            absolute: {
              point: 14.967359019193298,
              lower: 10.534758870048162,
              upper: 20.754349791764547,
            },
            difference: {},
            relative_uplift: {},
          },
          retained: {
            absolute: {
              point: 0.92610837438423643,
              lower: 0.88644814975695319,
              upper: 0.95784492649935471,
            },
            difference: {},
            relative_uplift: {},
          },
          picture_in_picture_ever_used: {
            absolute: {
              point: 0.05,
              count: 10,
              lower: 0.024357271316207685,
              upper: 0.084114637001734827,
            },
            difference: {},
            relative_uplift: {},
          },
          feature_b_ever_used: {
            absolute: {
              point: 0.05,
              count: 10,
              lower: 0.024357271316207685,
              upper: 0.084114637001734827,
            },
            difference: {},
            relative_uplift: {},
          },
          feature_c_ever_used: {
            absolute: {
              point: 0.05,
              count: 10,
              lower: 0.024357271316207685,
              upper: 0.084114637001734827,
            },
            difference: {},
            relative_uplift: {},
          },
        },
      },
      treatment: {
        is_control: true,
        branch_data: {
          identity: {
            absolute: {
              point: 200,
            },
            difference: {},
            relative_uplift: {},
            percent: 55,
          },
          search_count: {
            absolute: {
              point: 25.456361412643364,
              lower: 18.998951440573688,
              upper: 33.549291754637153,
            },
            difference: {
              point: 5.0758527676460012,
              upper: -5.63685604594333,
              lower: -15.289651027022447,
            },
            relative_uplift: {},
            significance: SIGNIFICANCE.NEGATIVE,
          },
          retained: {
            absolute: {
              point: 0.64215686274509809,
              lower: 0.57529460650836961,
              upper: 0.7063786618426765,
            },
            difference: {
              point: 0.032060163779913255,
              lower: -0.065023804214299957,
              upper: 0.12483606976999304,
            },
            relative_uplift: {},
            significance: SIGNIFICANCE.NEUTRAL,
          },
          picture_in_picture_ever_used: {
            absolute: {
              point: 0.049019607843137254,
              count: 10,
              lower: 0.023872203557007872,
              upper: 0.082490692094610241,
            },
            difference: {
              point: -0.00065694876288765341,
              upper: 0.043163817365120191,
              lower: 0.041750959639940292,
            },
            relative_uplift: {
              lower: -0.455210299676828,
              upper: 0.5104985718410426,
              point: -0.06233954570562385,
            },
            significance: SIGNIFICANCE.POSITIVE,
          },
          feature_b_ever_used: {
            absolute: {
              point: 0.049019607843137254,
              count: 10,
              lower: 0.023872203557007872,
              upper: 0.082490692094610241,
            },
            difference: {
              point: -0.00065694876288765341,
              upper: 0.043163817365120191,
              lower: 0.041750959639940292,
            },
            relative_uplift: {
              lower: -0.455210299676828,
              upper: 0.5104985718410426,
              point: -0.06233954570562385,
            },
            significance: SIGNIFICANCE.NEGATIVE,
          },
          feature_c_ever_used: {
            absolute: {
              point: 0.049019607843137254,
              count: 10,
              lower: 0.023872203557007872,
              upper: 0.082490692094610241,
            },
            difference: {
              point: -0.00065694876288765341,
              upper: 0.043163817365120191,
              lower: 0.041750959639940292,
            },
            relative_uplift: {
              lower: -0.455210299676828,
              upper: 0.5104985718410426,
              point: -0.06233954570562385,
            },
            significance: SIGNIFICANCE.NEUTRAL,
          },
        },
      },
    },
  },
  variants: [],
};
