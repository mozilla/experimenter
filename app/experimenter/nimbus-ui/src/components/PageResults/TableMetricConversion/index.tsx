/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  CONVERSION_METRIC_COLUMNS,
  DISPLAY_TYPE,
  GROUP,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import { AnalysisDataOverall } from "../../../lib/visualization/types";
import { getExtremeBounds } from "../../../lib/visualization/utils";
import { getConfig_nimbusConfig_outcomes } from "../../../types/getConfig";
import TableVisualizationRow from "../TableVisualizationRow";

type ConversionMetricStatistic = {
  name: string;
  displayType: DISPLAY_TYPE;
  branchComparison?: string;
  value?: string;
};

type TableMetricConversionProps = {
  results: AnalysisDataOverall;
  outcome: getConfig_nimbusConfig_outcomes;
  sortedBranches: string[];
};

const getStatistics = (slug: string): Array<ConversionMetricStatistic> => {
  const outcomeMetricID = `${slug}_ever_used`;

  // Make a copy of `CONVERSION_METRIC_COLUMNS` since we modify it.
  const conversionMetricStatisticsList = CONVERSION_METRIC_COLUMNS.map(
    (statistic: ConversionMetricStatistic) => {
      statistic["value"] = outcomeMetricID;
      return statistic;
    },
  );

  return conversionMetricStatisticsList;
};

const TableMetricConversion = ({
  results = {},
  outcome,
  sortedBranches,
}: TableMetricConversionProps) => {
  const conversionMetricStatistics = getStatistics(outcome.slug!);
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
            {CONVERSION_METRIC_COLUMNS.map((value) => (
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
                {conversionMetricStatistics.map(
                  ({ displayType, branchComparison, value }) => (
                    <TableVisualizationRow
                      key={`${displayType}-${value}`}
                      results={results[branch]}
                      group={GROUP.OTHER}
                      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
                      // isControlBranch={branch === controlBranchName}
                      {...{
                        metricKey,
                        displayType,
                        branchComparison,
                        bounds,
                      }}
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

export default TableMetricConversion;
