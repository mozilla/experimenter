/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  DISPLAY_TYPE,
  GROUP,
  PRIMARY_METRIC_COLUMNS,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import { AnalysisDataOverall } from "../../../lib/visualization/types";
import { getExtremeBounds } from "../../../lib/visualization/utils";
import { getConfig_nimbusConfig_outcomes } from "../../../types/getConfig";
import TableVisualizationRow from "../TableVisualizationRow";

type PrimaryMetricStatistic = {
  name: string;
  displayType: DISPLAY_TYPE;
  branchComparison?: string;
  value?: string;
};

type TableMetricPrimaryProps = {
  results: AnalysisDataOverall;
  outcome: getConfig_nimbusConfig_outcomes;
  sortedBranches: string[];
};

const getStatistics = (slug: string): Array<PrimaryMetricStatistic> => {
  const outcomeMetricID = `${slug}_ever_used`;

  // Make a copy of `PRIMARY_METRIC_COLUMNS` since we modify it.
  const primaryMetricStatisticsList = PRIMARY_METRIC_COLUMNS.map(
    (statistic: PrimaryMetricStatistic) => {
      statistic["value"] = outcomeMetricID;
      return statistic;
    },
  );

  return primaryMetricStatisticsList;
};

const TableMetricPrimary = ({
  results = {},
  outcome,
  sortedBranches,
}: TableMetricPrimaryProps) => {
  const primaryMetricStatistics = getStatistics(outcome.slug!);
  const metricKey = `${outcome.slug}_ever_used`;
  const bounds = getExtremeBounds(
    sortedBranches,
    results,
    outcome.slug!,
    GROUP.OTHER,
  );

  return (
    <div data-testid="table-metric-primary" className="mb-5">
      <h2 className="h5 mb-3" id={outcome.slug!}>
        {outcome.friendlyName}
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
                      group={GROUP.OTHER}
                      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
                      {...{ metricKey, displayType, branchComparison, bounds }}
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
