import { RESULT_COLUMN_TIPS } from "experimenter-rapid/components/visualization/constants/tooltips";

export enum SIGNIFICANCE {
  POSITIVE,
  NEGATIVE,
  NEUTRAL,
}

export const METRIC = {
  RETENTION: "retained",
  SEARCH: "search_count",
  USER_COUNT: "identity",
};

export const STATISTIC = {
  PERCENT: "percentage",
  BINOMIAL: "binomial",
  MEAN: "mean",
  COUNT: "count",
};

export const BRANCH_COMPARISON = {
  DIFFERENCE: "difference",
  UPLIFT: "relative_uplift",
};

// This is used as an ordered list of metrics to
// display in the results table from left to right.
export const RESULTS_METRICS_LIST = [
  {
    value: METRIC.RETENTION,
    name: "2-Week Browser Retention",
    tooltip: RESULT_COLUMN_TIPS.RETENTION,
  },
  {
    value: METRIC.SEARCH,
    name: "Daily Mean Searches Per User",
    tooltip: RESULT_COLUMN_TIPS.SEARCH,
  },
  {
    value: METRIC.USER_COUNT,
    name: "Total Users",
    tooltip: RESULT_COLUMN_TIPS.USER_COUNT,
  },
];
