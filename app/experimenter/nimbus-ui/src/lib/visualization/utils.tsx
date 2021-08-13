/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  BRANCH_COMPARISON,
  DISPLAY_TYPE,
  METRIC,
  TABLE_LABEL,
} from "./constants";
import {
  AnalysisData,
  AnalysisDataOverall,
  AnalysisDataWeekly,
  FormattedAnalysisPoint,
} from "./types";

// `show_analysis` is the feature flag for turning visualization on/off.
// `overall` and `weekly` will be `null` if the analysis isn't available yet.
export const analysisAvailable = (analysis: AnalysisData | undefined) =>
  analysis?.show_analysis && (analysis?.overall || analysis?.weekly);

export const analysisUnavailable = (analysis: AnalysisData | undefined) =>
  !analysisAvailable(analysis);

/**
 * The control/reference branch can be overridden in the Jetstream config. It's exposed in the
 * metadata in schema version 3+ and should be considered the "true" control branch used
 * when the analysis occurs.
 */
export const getControlBranchName = (analysis: AnalysisData) => {
  const { reference_branch: referenceBranch } = analysis.metadata || {};
  if (referenceBranch) {
    return referenceBranch;
  }
  const results = analysis.overall || analysis.weekly;
  for (const [branchName, branchData] of Object.entries(results!)) {
    if (branchData.is_control) {
      return branchName;
    }
  }
};

export const getTableDisplayType = (
  metricKey: string,
  tableLabel: string,
  isControl: boolean,
): DISPLAY_TYPE => {
  let displayType;
  switch (metricKey) {
    case METRIC.USER_COUNT:
      displayType = DISPLAY_TYPE.POPULATION;
      break;
    case METRIC.SEARCH:
    case METRIC.DAYS_OF_USE:
      if (tableLabel === TABLE_LABEL.RESULTS || isControl) {
        displayType = DISPLAY_TYPE.COUNT;
        break;
      }

    // fall through
    default:
      displayType = DISPLAY_TYPE.PERCENT;
  }

  return displayType;
};

// Returns [control/reference branch name, treatment branch names]
export const getSortedBranchNames = (analysis: AnalysisData) => {
  const controlBranchName = getControlBranchName(analysis);

  const unshiftControlBranch = (
    results: AnalysisDataOverall | AnalysisDataWeekly,
  ) => {
    const branches = Object.keys(results).filter(
      (branch) => branch !== controlBranchName,
    );
    branches.unshift(controlBranchName);
    return branches;
  };

  if (analysis.overall) {
    return unshiftControlBranch(analysis.overall);
  } else if (analysis.weekly) {
    return unshiftControlBranch(analysis.weekly);
  }
  return [];
};

/**
 * Find the most extreme upper or lower bound value
 * for an outcome across all branches.
 *
 * This is used to scale the confidence interval bars
 * shown for a metric.
 */
export const getExtremeBounds = (
  sortedBranches: string[],
  results: AnalysisDataOverall,
  outcomeSlug: string,
  group: string,
) => {
  let extreme = 0;
  sortedBranches.forEach((branch) => {
    const branchComparison = BRANCH_COMPARISON.UPLIFT;
    const metricDataList =
      results[branch].branch_data[group][outcomeSlug][branchComparison]["all"];
    metricDataList.forEach((dataPoint: FormattedAnalysisPoint) => {
      const { lower, upper } = dataPoint;
      const max = Math.max(Math.abs(lower!), Math.abs(upper!));
      extreme = max > extreme ? max : extreme;
    });
  });
  return extreme;
};
