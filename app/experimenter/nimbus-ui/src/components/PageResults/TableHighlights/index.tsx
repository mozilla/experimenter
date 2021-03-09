/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  BRANCH_COMPARISON,
  HIGHLIGHTS_METRICS_LIST,
  METRIC,
  METRICS_TIPS,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import { AnalysisData } from "../../../lib/visualization/types";
import { getTableDisplayType } from "../../../lib/visualization/utils";
import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_referenceBranch,
  getExperiment_experimentBySlug_treatmentBranches,
} from "../../../types/getExperiment";
import TableVisualizationRow from "../TableVisualizationRow";

type TableHighlightsProps = {
  primaryOutcomes: OutcomeSlugs;
  results: AnalysisData;
  experiment: getExperiment_experimentBySlug;
};

type Branch =
  | getExperiment_experimentBySlug_referenceBranch
  | getExperiment_experimentBySlug_treatmentBranches;

const getHighlightMetrics = (outcomes: OutcomeSlugs | null) => {
  // Make a copy of `HIGHLIGHTS_METRICS_LIST` since we modify it.
  const highlightMetricsList = [...HIGHLIGHTS_METRICS_LIST];
  outcomes?.forEach((outcome) => {
    highlightMetricsList.unshift({
      value: `${outcome!}_ever_used`,
      name: `${outcome!} conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
    });
  });

  return highlightMetricsList;
};

const getBranchDescriptions = (
  control: Branch | null,
  treatments: (Branch | null)[] | null,
) => {
  const branches = [control, ...(treatments || [])].filter(
    (branch): branch is Branch => branch !== null,
  );

  return branches.reduce(
    (descriptionsMap: { [branchSlug: string]: string }, branch: Branch) => {
      descriptionsMap[branch!.slug] = branch?.description;
      return descriptionsMap;
    },
    {},
  );
};

const TableHighlights = ({
  primaryOutcomes,
  results = {
    daily: [],
    weekly: {},
    overall: {},
    metadata: { metrics: {}, outcomes: {} },
    show_analysis: false,
  },
  experiment,
}: TableHighlightsProps) => {
  const highlightMetricsList = getHighlightMetrics(primaryOutcomes);
  const branchDescriptions = getBranchDescriptions(
    experiment.referenceBranch,
    experiment.treatmentBranches,
  );
  const overallResults = results?.overall!;

  return (
    <table data-testid="table-highlights" className="table mt-4 mb-0">
      <tbody>
        {Object.keys(overallResults).map((branch) => {
          const userCountMetric =
            overallResults[branch]["branch_data"][METRIC.USER_COUNT];
          const participantCount =
            userCountMetric[BRANCH_COMPARISON.ABSOLUTE]["first"]["point"];
          return (
            <tr key={branch} className="border-top">
              <th className="align-middle p-1 p-lg-3" scope="row">
                <p>{branch}</p>
                <p className="h6">
                  {participantCount} participants ({userCountMetric["percent"]}
                  %)
                </p>
              </th>
              <td className="p-1 p-lg-3 col-md-4 align-middle">
                {branchDescriptions[branch]}
              </td>
              {overallResults[branch]["is_control"] ? (
                <td className="p-1 p-lg-3 align-middle">
                  <div className="font-italic align-middle">---baseline---</div>
                </td>
              ) : (
                <td className="pt-3 px-3">
                  {highlightMetricsList.map((metric) => {
                    const metricKey = metric.value;
                    const displayType = getTableDisplayType(
                      metricKey,
                      TABLE_LABEL.HIGHLIGHTS,
                      overallResults[branch]["is_control"],
                    );
                    const tooltip =
                      results.metadata?.metrics[metricKey]?.description ||
                      metric.tooltip;
                    return (
                      <TableVisualizationRow
                        key={`${displayType}-${metricKey}`}
                        metricName={metric.name}
                        results={overallResults[branch]}
                        tableLabel={TABLE_LABEL.HIGHLIGHTS}
                        {...{ metricKey, displayType, tooltip }}
                      />
                    );
                  })}
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default TableHighlights;
