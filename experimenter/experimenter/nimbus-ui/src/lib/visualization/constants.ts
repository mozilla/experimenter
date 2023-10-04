/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export const METRICS_TIPS = {
  RETENTION: "Percentage of users who returned to Firefox two weeks later",
  SEARCH: "Daily mean number of searches per user",
  USER_COUNT:
    "Total users in a variant and the % of users out of the entire experiment population",
  CONVERSION: "Percentage of users in the variant who used this feature",
  DAYS_OF_USE: "Average number of days each client sent a main ping",
  QUALIFIED_CUMULATIVE_DAYS_OF_USE:
    "Average number of days each client sent a main ping",
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
  USER_SELECTED_SECONDARY_METRIC:
    "Additional metric chosen by experiment owner for context. Not the main metric you are trying to impact in this experiment",
  DEFAULT_SECONDARY_METRIC:
    "Additional metric processed by default for all experiments. Not the main metric you are trying to impact in this experiment",
  GUARDRAIL_METRIC: "Metric that should not regress",
};

export const GENERAL_TIPS = {
  MISSING_RETENTION:
    "Retention is only available after at least 1 week of data post enrollment",
  EARLY_RESULTS:
    "WARNING: Experiment is not complete. Do not end the experiment early based on these results without consulting a Data Scientist.",
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
  DAYS_OF_USE: "days_of_use",
  USER_COUNT: "identity",
  QUALIFIED_CUMULATIVE_DAYS_OF_USE: "qualified_cumulative_days_of_use",
};

export const METRIC_TYPE = {
  PRIMARY: {
    label: "Primary Metric",
    badge: "badge-primary",
    tooltip: BADGE_TIPS.PRIMARY_METRIC,
  },
  USER_SELECTED_SECONDARY: {
    label: "User-Selected Secondary Metric",
    badge: "badge-warning",
    tooltip: BADGE_TIPS.USER_SELECTED_SECONDARY_METRIC,
  },
  DEFAULT_SECONDARY: {
    label: "Default Secondary Metric",
    badge: "badge-warning",
    tooltip: BADGE_TIPS.DEFAULT_SECONDARY_METRIC,
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
} as const;

export const BRANCH_COMPARISON_TITLE = {
  ABSOLUTE: "Absolute",
  DIFFERENCE: "Difference",
  UPLIFT: "Relative Uplift",
};

export const TABLE_LABEL = {
  HIGHLIGHTS: "highlights",
  RESULTS: "results",
  PRIMARY_METRICS: "primary_metrics",
  SECONDARY_METRICS: "secondary_metrics",
};

export const GROUP = {
  SEARCH: "search_metrics",
  USAGE: "usage_metrics",
  OTHER: "other_metrics",
};

const GROUPED_METRICS = [
  {
    name: GROUP.SEARCH,
    metrics: [
      "searches_with_ads",
      "search_count", // Remove this when guardrail metrics are added.
      "organic_search_count",
      "tagged_follow_on_search_count",
      "tagged_search_count",
    ],
  },
  {
    name: GROUP.USAGE,
    metrics: ["uri_count", "active_hours"],
  },
  {
    name: GROUP.OTHER,
    metrics: [
      "retained",
      "identity",
      "days_of_use",
      "qualified_cumulative_days_of_use",
    ],
  },
];

export const METRIC_TO_GROUP = GROUPED_METRICS.reduce((res, group) => {
  group.metrics.forEach((metric) => {
    res[metric] = group.name;
  });
  return res;
}, {} as Record<string, string>);

// This is used as an ordered list of items to
// display in the highlights table from top to bottom.
export const HIGHLIGHTS_METRICS_LIST = [
  {
    value: METRIC.RETENTION,
    name: "Retention",
    tooltip: METRICS_TIPS.RETENTION,
    group: METRIC_TO_GROUP[METRIC.RETENTION],
  },
  {
    value: METRIC.SEARCH,
    name: "Search",
    tooltip: METRICS_TIPS.SEARCH,
    group: METRIC_TO_GROUP[METRIC.SEARCH],
  },
  {
    value: METRIC.DAYS_OF_USE,
    name: "Days of Use",
    tooltip: METRICS_TIPS.DAYS_OF_USE,
    group: METRIC_TO_GROUP[METRIC.DAYS_OF_USE],
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
    group: METRIC_TO_GROUP[METRIC.RETENTION],
  },
  {
    value: METRIC.SEARCH,
    name: "Mean Searches Per User",
    tooltip: METRICS_TIPS.SEARCH,
    type: METRIC_TYPE.GUARDRAIL,
    group: METRIC_TO_GROUP[METRIC.SEARCH],
  },
  {
    value: METRIC.DAYS_OF_USE,
    name: "Overall Mean Days of Use Per User",
    tooltip: METRICS_TIPS.DAYS_OF_USE,
    type: METRIC_TYPE.GUARDRAIL,
    group: METRIC_TO_GROUP[METRIC.DAYS_OF_USE],
  },
  {
    value: METRIC.USER_COUNT,
    name: "Total Users",
    tooltip: METRICS_TIPS.USER_COUNT,
    group: METRIC_TO_GROUP[METRIC.USER_COUNT],
  },
];

// This is used as an ordered list of items to
// display in the conversion metric table from left to right.
export const CONVERSION_METRIC_COLUMNS = [
  {
    name: "Conversions / Total Users",
    displayType: DISPLAY_TYPE.CONVERSION_COUNT,
    branchComparison: BRANCH_COMPARISON.ABSOLUTE,
  },
  {
    name: "Absolute Conversion Rate",
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
// display in the count metric table from left to right.
export const COUNT_METRIC_COLUMNS = [
  {
    name: "Absolute Count",
    displayType: DISPLAY_TYPE.COUNT,
    branchComparison: BRANCH_COMPARISON.ABSOLUTE,
  },
  {
    name: "Relative Improvement",
    displayType: DISPLAY_TYPE.CONVERSION_CHANGE,
    branchComparison: BRANCH_COMPARISON.UPLIFT,
  },
];
