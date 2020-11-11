/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export const METRICS_TIPS = {
  RETENTION: "Percentage of users w ho returned to Firefox two weeks later",
  SEARCH: "Daily mean number of searches per user",
  USER_COUNT:
    "Total users in a variant and the % of users out of the entire experiment population",
  CONVERSION: "Percentage of users in the variant who used this feature",
};

export const SEGMENT_TIPS = {
  ALL_USERS: "All users within a given variant",
};

export const SIGNIFICANCE_TIPS = {
  POSITIVE: "Treatment variant is significantly better than control variant",
  NEGATIVE: "Treatment variant is significantly worse than control variant",
  NEUTRAL:
    "Treatment variant has no significant difference relative to control variant",
};

export enum VARIANT_TYPE {
  CONTROL,
  VARIANT,
}

export enum DISPLAY_TYPE {
  POPULATION,
  PERCENT,
  COUNT,
  CONVERSION_COUNT,
  CONVERSION_RATE,
  CONVERSION_CHANGE,
}

export const SIGNIFICANCE = {
  POSITIVE: "positive",
  NEGATIVE: "negative",
  NEUTRAL: "neutral",
};

export const METRIC = {
  RETENTION: "retained",
  SEARCH: "search_count",
  USER_COUNT: "identity",
};

export const HIGHLIGHTS_METRICS_LIST = [
  {
    value: METRIC.RETENTION,
    name: "Retention",
    tooltip: METRICS_TIPS.RETENTION,
  },
  {
    value: METRIC.SEARCH,
    name: "Search",
    tooltip: METRICS_TIPS.SEARCH,
  },
];

export const BRANCH_COMPARISON = {
  ABSOLUTE: "absolute",
  DIFFERENCE: "difference",
  UPLIFT: "relative_uplift",
};

export const TABLE_LABEL = {
  HIGHLIGHTS: "highlights",
  RESULTS: "results",
  PRIMARY_METRICS: "primary_metrics",
};
