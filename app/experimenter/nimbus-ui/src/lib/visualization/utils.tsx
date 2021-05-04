/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { DISPLAY_TYPE, METRIC, TABLE_LABEL } from "./constants";
import { AnalysisData, BranchDescription } from "./types";

// `show_analysis` is the feature flag for turning visualization on/off.
// `overall` will be `null` if the analysis isn't available yet.
export const analysisAvailable = (analysis: AnalysisData | undefined) =>
  analysis?.show_analysis && (analysis?.overall || analysis?.weekly);

export const analysisUnavailable = (analysis: AnalysisData | undefined) =>
  analysis && !analysisAvailable(analysis);

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

export const getSortedBranches = (analysis: AnalysisData) => {
  const results: { [branch: string]: BranchDescription } | null =
    analysis?.overall || analysis?.weekly;
  if (!results) {
    return [];
  }

  const sortedBranches: string[] = [];
  Object.keys(results).forEach((branch: string) => {
    if (results[branch]["is_control"]) {
      sortedBranches.unshift(branch);
    } else {
      sortedBranches.push(branch);
    }
  });
  return sortedBranches;
};
