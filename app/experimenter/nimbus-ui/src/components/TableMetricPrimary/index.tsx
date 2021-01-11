/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { AnalysisDataOverall } from "../../lib/visualization/types";
import TableVisualizationRow from "../TableVisualizationRow";
import { getExperiment_experimentBySlug_primaryProbeSets } from "../../types/getExperiment";
import {
  PRIMARY_METRIC_COLUMNS,
  TABLE_LABEL,
  DISPLAY_TYPE,
} from "../../lib/visualization/constants";

type PrimaryMetricStatistic = {
  name: string;
  displayType: DISPLAY_TYPE;
  branchComparison?: string;
  value?: string;
};

type TableMetricPrimaryProps = {
  results: AnalysisDataOverall;
  probeSet: getExperiment_experimentBySlug_primaryProbeSets;
};

const getStatistics = (slug: string): Array<PrimaryMetricStatistic> => {
  const probesetMetricID = `${slug}_ever_used`;

  // Make a copy of `PRIMARY_METRIC_COLUMNS` since we modify it.
  const primaryMetricStatisticsList = PRIMARY_METRIC_COLUMNS.map(
    (statistic: PrimaryMetricStatistic) => {
      statistic["value"] = probesetMetricID;
      return statistic;
    },
  );

  return primaryMetricStatisticsList;
};

const TableMetricPrimary = ({
  results = {},
  probeSet,
}: TableMetricPrimaryProps) => {
  const primaryMetricStatistics = getStatistics(probeSet!.slug);
  const metricKey = `${probeSet.slug}_ever_used`;

  return (
    <div data-testid="table-metric-primary">
      <h2 className="h5 mb-3" id={probeSet.slug}>
        {probeSet.name}
      </h2>
      <table className="table-visualization-center">
        <thead>
          <tr>
            <th scope="col" className="border-bottom-0 bg-light" />
            {PRIMARY_METRIC_COLUMNS.map((value) => (
              <th
                className="border-bottom-0 bg-light"
                key={value.name}
                scope="col"
              >
                <div>{value.name}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.keys(results).map((branch) => {
            return (
              <tr key={branch}>
                <th className="align-middle" scope="row">
                  {branch}
                </th>
                {primaryMetricStatistics.map(
                  ({ displayType, branchComparison, value }) => (
                    <TableVisualizationRow
                      key={`${displayType}-${value}`}
                      results={results[branch]}
                      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
                      {...{ metricKey, displayType, branchComparison }}
                    />
                  ),
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default TableMetricPrimary;
