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
  Metadata,
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
export const getControlBranchName = (
  { reference_branch }: { reference_branch: Metadata["reference_branch"] },
  results: AnalysisDataOverall | AnalysisDataWeekly,
) => {
  if (reference_branch) {
    return reference_branch;
  }
  for (const [branchName, branchData] of Object.entries(results)) {
    if (branchData.is_control) {
      return branchName;
    }
  }
  // we should never get here in practice
  return "";
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

// Ensures the control branch is first
export const getSortedBranches = (analysis: AnalysisData) => {
  if (analysis.overall) {
    return Object.keys(analysis.overall)
      .filter((branch) => analysis.overall?.[branch].is_control)
      .concat(
        Object.keys(analysis.overall).filter(
          (branch) => !analysis.overall?.[branch].is_control,
        ),
      );
  } else if (analysis.weekly) {
    return Object.keys(analysis.weekly)
      .filter((branch) => analysis.weekly?.[branch].is_control)
      .concat(
        Object.keys(analysis.weekly).filter(
          (branch) => !analysis.weekly?.[branch].is_control,
        ),
      );
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
