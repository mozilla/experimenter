/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import TableVisualizationRow from "src/components/PageResults/TableVisualizationRow";
import TooltipWithMarkdown from "src/components/PageResults/TooltipWithMarkdown";
import { useOutcomes } from "src/hooks";
import { ResultsContext } from "src/lib/contexts";
import { OutcomesList } from "src/lib/types";
import {
  BRANCH_COMPARISON,
  GROUP,
  METRICS_TIPS,
  METRIC_TYPE,
  RESULTS_METRICS_LIST,
  TABLE_LABEL,
} from "src/lib/visualization/constants";
import {
  AnalysisBases,
  BranchComparisonValues,
} from "src/lib/visualization/types";
import { getTableDisplayType } from "src/lib/visualization/utils";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

export type TableResultsProps = {
  experiment: getExperiment_experimentBySlug;
  branchComparison?: BranchComparisonValues;
  analysisBasis?: AnalysisBases;
  segment?: string;
};

const getResultMetrics = (outcomes: OutcomesList) => {
  // Make a copy of `RESULTS_METRICS_LIST` since we modify it.
  const resultsMetricsList = [...RESULTS_METRICS_LIST];
  outcomes?.forEach((outcome) => {
    if (!outcome?.isDefault) {
      return;
    }
    resultsMetricsList.unshift({
      value: `${outcome!.slug}_ever_used`,
      name: `${outcome!.friendlyName} Conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
      type: METRIC_TYPE.PRIMARY,
      group: GROUP.OTHER,
    });
  });

  return resultsMetricsList;
};

const TableResults = ({
  experiment,
  branchComparison = BRANCH_COMPARISON.UPLIFT,
  analysisBasis = "enrollments",
  segment = "all",
}: TableResultsProps) => {
  const { primaryOutcomes } = useOutcomes(experiment);
  const resultsMetricsList = getResultMetrics(primaryOutcomes);
  const {
    analysis: { metadata, overall },
    sortedBranchNames,
    controlBranchName,
  } = useContext(ResultsContext);
  const overallResults = overall![analysisBasis]?.[segment]!;

  return (
    <table
      className="table-visualization-center mb-0 border-bottom-0"
      data-testid="table-results"
    >
      <thead>
        <tr>
          <th scope="col" className="border-bottom-0 bg-light" />
          {resultsMetricsList.map((metric, index) => {
            const badgeClass = `badge ${metric.type?.badge}`;
            const outcomeDescription =
              metadata?.metrics[metric.value]?.description || metric.tooltip;

            return (
              <th
                key={`${metric.type}-${index}`}
                scope="col"
                className="border-bottom-0 align-middle bg-light"
              >
                <h3 className="h6 mb-0" data-tip data-for={metric.value}>
                  {metric.name}
                </h3>
                <TooltipWithMarkdown
                  tooltipId={metric.value}
                  markdown={outcomeDescription}
                />
                {metric.type && (
                  <span className={badgeClass} data-tip={metric.type.tooltip}>
                    {metric.type.label}
                  </span>
                )}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        {sortedBranchNames.map((branch) => {
          const isControlBranch = branch === controlBranchName;
          return (
            <tr key={branch}>
              <th className="align-middle" scope="row">
                {branch}
              </th>
              {resultsMetricsList.map((metric) => {
                const metricKey = metric.value;
                const displayType = getTableDisplayType(
                  metricKey,
                  branchComparison,
                );
                return (
                  <TableVisualizationRow
                    key={`${displayType}-${metricKey}`}
                    metricName={metric.name}
                    results={overallResults[branch]}
                    group={metric.group}
                    tableLabel={TABLE_LABEL.RESULTS}
                    {...{
                      metricKey,
                      displayType,
                      branchComparison,
                      isControlBranch,
                    }}
                  />
                );
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default TableResults;
