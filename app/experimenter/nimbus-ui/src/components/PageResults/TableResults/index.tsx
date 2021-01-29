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
import { AnalysisDataOverall } from "../../../lib/visualization/types";
import { getTableDisplayType } from "../../../lib/visualization/utils";
import { getExperiment_experimentBySlug_primaryProbeSets } from "../../../types/getExperiment";
import TableVisualizationRow from "../TableVisualizationRow";

type TableResultsProps = {
  primaryProbeSets: (getExperiment_experimentBySlug_primaryProbeSets | null)[];
  results: AnalysisDataOverall;
};

const getResultMetrics = (
  probeSets: (getExperiment_experimentBySlug_primaryProbeSets | null)[],
) => {
  // Make a copy of `RESULTS_METRICS_LIST` since we modify it.
  const resultsMetricsList = [...RESULTS_METRICS_LIST];
  probeSets.forEach((probeSet) => {
    resultsMetricsList.unshift({
      value: `${probeSet!.slug}_ever_used`,
      name: `${probeSet!.name} Conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
      type: METRIC_TYPE.PRIMARY,
    });
  });

  return resultsMetricsList;
};

const TableResults = ({
  primaryProbeSets,
  results = {},
}: TableResultsProps) => {
  const resultsMetricsList = getResultMetrics(primaryProbeSets);

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
            return (
              <th
                key={`${metric.type}-${index}`}
                scope="col"
                className="border-bottom-0 align-middle bg-light"
              >
                <h3 className="h6 mb-0" data-tip={metric.tooltip}>
                  {metric.name}
                </h3>
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
        {Object.keys(results).map((branch) => {
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
                  results[branch]["is_control"],
                );
                return (
                  <TableVisualizationRow
                    key={`${displayType}-${metricKey}`}
                    metricName={metric.name}
                    results={results[branch]}
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
