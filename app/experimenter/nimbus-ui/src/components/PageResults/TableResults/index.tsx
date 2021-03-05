/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  METRICS_TIPS,
  METRIC_TYPE,
  RESULTS_METRICS_LIST,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import { AnalysisData } from "../../../lib/visualization/types";
import { getTableDisplayType } from "../../../lib/visualization/utils";
import TableVisualizationRow from "../TableVisualizationRow";
import TooltipWithMarkdown from "../TooltipWithMarkdown";

type TableResultsProps = {
  primaryOutcomes: (string | null)[] | null;
  results: AnalysisData;
};

const getResultMetrics = (outcomes: (string | null)[] | null) => {
  // Make a copy of `RESULTS_METRICS_LIST` since we modify it.
  const resultsMetricsList = [...RESULTS_METRICS_LIST];
  outcomes.forEach((outcome) => {
    resultsMetricsList.unshift({
      value: `${outcome}_ever_used`,
      name: `${outcome} Conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
      type: METRIC_TYPE.PRIMARY,
    });
  });

  return resultsMetricsList;
};

const TableResults = ({
  primaryOutcomes,
  results = {
    daily: [],
    weekly: {},
    overall: {},
    metadata: { metrics: {}, probesets: {} },
    show_analysis: false,
  },
}: TableResultsProps) => {
  const resultsMetricsList = getResultMetrics(primaryOutcomes);
  const overallResults = results?.overall!;

  return (
    <table
      className="table-visualization-center mb-5"
      data-testid="table-results"
    >
      <thead>
        <tr>
          <th scope="col" className="border-bottom-0 bg-light" />
          {resultsMetricsList.map((metric, index) => {
            const badgeClass = `badge ${metric.type?.badge}`;
            const probeSetDescription =
              results.metadata?.metrics[metric.value]?.description ||
              metric.tooltip;

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
                  markdown={probeSetDescription}
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
        {Object.keys(overallResults).map((branch) => {
          return (
            <tr key={branch}>
              <th className="align-middle" scope="row">
                {branch}
              </th>
              {resultsMetricsList.map((metric) => {
                const metricKey = metric.value;
                const displayType = getTableDisplayType(
                  metricKey,
                  TABLE_LABEL.RESULTS,
                  overallResults[branch]["is_control"],
                );
                return (
                  <TableVisualizationRow
                    key={`${displayType}-${metricKey}`}
                    metricName={metric.name}
                    results={overallResults[branch]}
                    tableLabel={TABLE_LABEL.RESULTS}
                    {...{ metricKey }}
                    {...{ displayType }}
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
