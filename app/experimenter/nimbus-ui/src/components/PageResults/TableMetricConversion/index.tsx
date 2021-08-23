/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import { ResultsContext } from "../../../lib/contexts";
import {
  CONVERSION_METRIC_COLUMNS,
  DISPLAY_TYPE,
  GROUP,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
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
  outcome: getConfig_nimbusConfig_outcomes;
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

const TableMetricConversion = ({ outcome }: TableMetricConversionProps) => {
  const {
    analysis: { overall },
    sortedBranchNames,
    controlBranchName,
  } = useContext(ResultsContext);
  const overallResults = overall!;
  const conversionMetricStatistics = getStatistics(outcome.slug!);
  const metricKey = `${outcome.slug}_ever_used`;
  const bounds = getExtremeBounds(
    sortedBranchNames,
    overallResults,
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
          {Object.keys(overallResults).map((branch) => {
            const isControlBranch = branch === controlBranchName;
            return (
              <tr key={branch}>
                <th className="align-middle" scope="row">
                  {branch}
                </th>
                {conversionMetricStatistics.map(
                  ({ displayType, branchComparison, value }) => (
                    <TableVisualizationRow
                      key={`${displayType}-${value}`}
                      results={overallResults[branch]}
                      group={GROUP.OTHER}
                      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
                      {...{
                        metricKey,
                        displayType,
                        branchComparison,
                        bounds,
                        isControlBranch,
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
