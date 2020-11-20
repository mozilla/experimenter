/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export const METRICS_TIPS = {
  RETENTION: "Percentage of users who returned to Firefox two weeks later",
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

export const BADGE_TIPS = {
  PRIMARY_METRIC: "Main metric you are trying to impact in this experiment",
  GUARDRAIL_METRIC: "Metric that should not regress",
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

export const METRIC_TYPE = {
  PRIMARY: {
    label: "Primary Metric",
    badge: "badge-primary",
    tooltip: BADGE_TIPS.PRIMARY_METRIC,
  },
  SECONDARY: {
    label: "Secondary Metric",
    badge: "badge-secondary",
  },
  GUARDRAIL: {
    label: "Guardrail Metric",
    badge: "badge-warning",
    tooltip: BADGE_TIPS.GUARDRAIL_METRIC,
  },
};

export const BRANCH_COMPARISON = {
  ABSOLUTE: "absolute",
  DIFFERENCE: "difference",
  UPLIFT: "relative_uplift",
};

export const TABLE_LABEL = {
  HIGHLIGHTS: "highlights",
  RESULTS: "results",
  PRIMARY_METRICS: "primary_metrics",
  SECONDARY_METRICS: "secondary_metrics",
};

// This is used as an ordered list of items to
// display in the highlights table from top to bottom.
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

// This is used as an ordered list of metrics to
// display in the results table from left to right.
export const RESULTS_METRICS_LIST = [
  {
    value: METRIC.RETENTION,
    name: "2-Week Browser Retention",
    tooltip: METRICS_TIPS.RETENTION,
    type: METRIC_TYPE.GUARDRAIL,
  },
  {
    value: METRIC.SEARCH,
    name: "Daily Mean Searches Per User",
    tooltip: METRICS_TIPS.SEARCH,
    type: METRIC_TYPE.GUARDRAIL,
  },
  {
    value: METRIC.USER_COUNT,
    name: "Total Users",
    tooltip: METRICS_TIPS.USER_COUNT,
  },
];

// This is used as an ordered list of items to
// display in the primary metric table from left to right.
export const PRIMARY_METRIC_COLUMNS = [
  {
    name: "Conversions / Total Users",
    displayType: DISPLAY_TYPE.CONVERSION_COUNT,
  },
  {
    name: "Conversion Rate",
    displayType: DISPLAY_TYPE.CONVERSION_RATE,
    branchComparison: BRANCH_COMPARISON.ABSOLUTE,
  },
  {
    name: "Relative Improvement",
    displayType: DISPLAY_TYPE.CONVERSION_CHANGE,
    branchComparison: BRANCH_COMPARISON.UPLIFT,
  },
];

// This is used as an ordered list of items to
// display in the secondary metric table from left to right.
export const SECONDARY_METRIC_COLUMNS = [
  {
    name: "Count",
    displayType: DISPLAY_TYPE.COUNT,
    branchComparison: BRANCH_COMPARISON.ABSOLUTE,
  },
  {
    name: "Relative Improvement",
    displayType: DISPLAY_TYPE.CONVERSION_CHANGE,
    branchComparison: BRANCH_COMPARISON.UPLIFT,
  },
];
