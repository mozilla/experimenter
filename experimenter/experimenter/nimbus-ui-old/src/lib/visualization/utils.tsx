/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  BRANCH_COMPARISON,
  DISPLAY_TYPE,
  METRIC,
  METRIC_TO_GROUP,
} from "src/lib/visualization/constants";
import {
  AnalysisData,
  AnalysisDataOverall,
  BranchComparisonValues,
  BranchDescription,
  FormattedAnalysisPoint,
} from "src/lib/visualization/types";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

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

  throw new Error(
    "Invalid argument 'analysis': no branch name could be found in the results.",
  );
};

// Returns [control/reference branch name, treatment branch names]
export const getSortedBranchNames = (
  analysis: AnalysisData,
  experiment: getExperiment_experimentBySlug | null,
) => {
  const branches: string[] = [];
  try {
    let configuredReferenceBranch = "";
    const configuredBranches: string[] = [];
    let analysisControlBranch = "";

    let actualControlBranch = "";
    if (
      experiment &&
      experiment.referenceBranch &&
      experiment.treatmentBranches
    ) {
      configuredReferenceBranch = experiment.referenceBranch.slug;
      configuredBranches.push(configuredReferenceBranch);
      configuredBranches.push(
        ...experiment.treatmentBranches.map((b) => b!.slug),
      );
    }
    // cross-reference reference branch (prefer analysis data here in case of overrides)
    try {
      analysisControlBranch = getControlBranchName(analysis)!;
    } catch (_e) {}
    if (
      configuredReferenceBranch !== analysisControlBranch &&
      (analysisControlBranch === "" ||
        !configuredBranches.includes(analysisControlBranch))
    ) {
      actualControlBranch = configuredReferenceBranch;
    } else {
      actualControlBranch = analysisControlBranch;
    }

    // cross-reference treatment branches (prefer configured here in case of erroneous
    // branch data in results -- e.g., from QA)
    const results =
      analysis.overall?.enrollments?.all ||
      analysis.weekly?.enrollments?.all ||
      {};
    const analysisBranches = [
      actualControlBranch,
      ...Object.keys(results).filter(
        (branch) => branch !== actualControlBranch,
      ),
    ];
    branches.push(
      ...analysisBranches.filter((branch) =>
        configuredBranches.includes(branch),
      ),
    );
  } catch (_e) {}
  return branches;
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
  referenceBranch: string,
) => {
  let extreme = 0;
  sortedBranchNames.forEach((branch) => {
    if (results![segment]![branch].branch_data[group][outcomeSlug]) {
      results![segment]![branch].branch_data[group][outcomeSlug][
        BRANCH_COMPARISON.UPLIFT
      ][referenceBranch]["all"].forEach((dataPoint: FormattedAnalysisPoint) => {
        const { lower, upper } = dataPoint;
        const max = Math.max(Math.abs(lower!), Math.abs(upper!));
        extreme = max > extreme ? max : extreme;
      });
    }
  });
  return extreme;
};

/**
 * Determine whether UI should fallback to using DOU instead of DAU.
 *
 * @param results BranchDescription to search for DOU and DAU
 * @returns true if `results` contains DOU but not DAU results, else false
 */
export const shouldUseDou = (results: BranchDescription | undefined) => {
  if (!results) {
    return false;
  }
  const dauGroup = METRIC_TO_GROUP[METRIC.DAILY_ACTIVE_USERS];
  const douGroup = METRIC_TO_GROUP[METRIC.DAYS_OF_USE];
  try {
    // DAU is not guaranteed to have `absolute` data so we'll check the branch comparison data
    if (METRIC.DAILY_ACTIVE_USERS in results.branch_data[dauGroup]) {
      for (const branch in results.branch_data[dauGroup][
        METRIC.DAILY_ACTIVE_USERS
      ].difference) {
        if (
          results.branch_data[dauGroup][METRIC.DAILY_ACTIVE_USERS].difference[
            branch
          ].all.length > 0
        ) {
          // found DAU -- don't use DOU
          return false;
        }
      }
    }
    // DOU should always have `absolute` data
    if (METRIC.DAYS_OF_USE in results.branch_data[douGroup]) {
      // didn't find DAU, return true if DOU data exists
      return (
        results.branch_data[dauGroup][METRIC.DAYS_OF_USE].absolute.all.length >
        0
      );
    }
  } catch (e) {
    // if there is some problem traversing the results, we default to false
    return false;
  }

  // found neither DOU or DAU, default to DAU
  return false;
};
