/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { BRANCH_COMPARISON, DISPLAY_TYPE, METRIC } from "./constants";
import {
  AnalysisData,
  AnalysisDataOverall,
  BranchComparisonValues,
  FormattedAnalysisPoint,
} from "./types";

// `show_analysis` is the feature flag for turning visualization on/off.
// `overall` and `weekly` will be `null` if the analysis isn't available yet.
export const analysisAvailable = (analysis: AnalysisData | undefined) =>
  analysis?.show_analysis && (analysis?.overall || analysis?.weekly);

export const analysisUnavailable = (analysis: AnalysisData | undefined) =>
  analysis && !analysisAvailable(analysis);

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
  const results = analysis.overall || analysis.weekly;
  for (const [branchName, branchData] of Object.entries(results!)) {
    if (branchData.is_control) {
      return branchName;
    }
  }
};

// Returns [control/reference branch name, treatment branch names]
export const getSortedBranchNames = (analysis: AnalysisData) => {
  const controlBranchName = getControlBranchName(analysis)!;
  const results = analysis.overall || analysis.weekly || {};
  return [
    controlBranchName,
    ...Object.keys(results).filter((branch) => branch !== controlBranchName),
  ];
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
) => {
  let extreme = 0;
  sortedBranchNames.forEach((branch) => {
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
