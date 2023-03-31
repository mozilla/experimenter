/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  BRANCH_COMPARISON,
  DISPLAY_TYPE,
  METRIC,
} from "src/lib/visualization/constants";
import {
  AnalysisData,
  AnalysisDataOverall,
  BranchComparisonValues,
  FormattedAnalysisPoint,
} from "src/lib/visualization/types";

export const getTableDisplayType = (
  metricKey: string,
  branchComparison: BranchComparisonValues,
): DISPLAY_TYPE => {
  // User count metrics always display as "population" and retention metrics
  // always display as "percent" despite the branch comparison.
  if (metricKey === METRIC.USER_COUNT) return DISPLAY_TYPE.POPULATION;
  if (metricKey === METRIC.RETENTION) return DISPLAY_TYPE.PERCENT;
  if (branchComparison === BRANCH_COMPARISON.ABSOLUTE) {
    return DISPLAY_TYPE.COUNT;
  } else {
    return DISPLAY_TYPE.PERCENT;
  }
};

export const getControlBranchName = (analysis: AnalysisData) => {
  const { external_config } = analysis.metadata || {};
  if (external_config?.reference_branch) {
    return external_config.reference_branch;
  }
  const results =
    analysis.overall?.enrollments?.all ||
    analysis.weekly?.enrollments?.all ||
    {};
  if (Object.keys(results).length > 0) {
    for (const [branchName, branchData] of Object.entries(results)) {
      if (branchData.is_control) {
        return branchName;
      }
    }
  }
  // last option - try to find a unique branch name in the daily results
  const daily = analysis.daily?.enrollments?.all || [];
  if (daily.length > 0) {
    const branches = new Set(daily.map((point) => point.branch));
    if (branches.size === 1) {
      return branches.values().next().value; // return the first and only value
    }
  }

  throw new Error(
    "Invalid argument 'analysis': no branch name could be found in the results.",
  );
};

// Returns [control/reference branch name, treatment branch names]
export const getSortedBranchNames = (analysis: AnalysisData) => {
  try {
    const controlBranchName = getControlBranchName(analysis)!;
    const results =
      analysis.overall?.enrollments?.all ||
      analysis.weekly?.enrollments?.all ||
      {};
    return [
      controlBranchName,
      ...Object.keys(results).filter((branch) => branch !== controlBranchName),
    ];
  } catch (_e) {
    return [];
  }
};

/**
 * Find the most extreme upper or lower bound value
 * for an outcome across all branches.
 *
 * This is used to scale the confidence interval bars
 * shown for a metric.
 */
export const getExtremeBounds = (
  sortedBranchNames: string[],
  results: AnalysisDataOverall,
  outcomeSlug: string,
  group: string,
  segment: string,
) => {
  let extreme = 0;
  sortedBranchNames.forEach((branch) => {
    if (results![segment]![branch].branch_data[group][outcomeSlug]) {
      results![segment]![branch].branch_data[group][outcomeSlug][
        BRANCH_COMPARISON.UPLIFT
      ]["all"].forEach((dataPoint: FormattedAnalysisPoint) => {
        const { lower, upper } = dataPoint;
        const max = Math.max(Math.abs(lower!), Math.abs(upper!));
        extreme = max > extreme ? max : extreme;
      });
    }
  });
  return extreme;
};
