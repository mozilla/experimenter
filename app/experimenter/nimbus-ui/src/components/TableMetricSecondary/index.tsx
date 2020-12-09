/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  DISPLAY_TYPE,
  SECONDARY_METRIC_COLUMNS,
  TABLE_LABEL,
  METRIC_TYPE,
} from "../../lib/visualization/constants";
import { AnalysisData } from "../../lib/visualization/types";
import TableVisualizationRow from "../TableVisualizationRow";

type SecondaryMetricStatistic = {
  name: string;
  displayType: DISPLAY_TYPE;
  branchComparison?: string;
  value?: string;
};

type TableMetricSecondaryProps = {
  results: AnalysisData["overall"];
  probeSetSlug: string;
  probeSetName: string;
  isDefault?: boolean;
};

const getStatistics = (slug: string): Array<SecondaryMetricStatistic> => {
  // Make a copy of `SECONDARY_METRIC_COLUMNS` since we modify it.
  const secondaryMetricStatisticsList = SECONDARY_METRIC_COLUMNS.map(
    (statistic: SecondaryMetricStatistic) => {
      statistic["value"] = slug;
      return statistic;
    },
  );

  return secondaryMetricStatisticsList;
};

const TableMetricSecondary = ({
  results = {},
  probeSetSlug,
  probeSetName,
  isDefault = true,
}: TableMetricSecondaryProps) => {
  const secondaryMetricStatistics = getStatistics(probeSetSlug);
  const secondaryType = isDefault
    ? METRIC_TYPE.DEFAULT_SECONDARY
    : METRIC_TYPE.USER_SELECTED_SECONDARY;

  return (
    <div data-testid="table-metric-secondary">
      <h2 className="h5 mb-3">
        <div>{probeSetName}</div>
        <div
          className={`badge ${secondaryType.badge}`}
          data-tip={secondaryType.tooltip}
        >
          {secondaryType.label}
        </div>
      </h2>

      <table className="table-visualization-center">
        <thead>
          <tr>
            <th scope="col" className="border-bottom-0 bg-light" />
            {SECONDARY_METRIC_COLUMNS.map((value) => (
              <th
                key={value.name}
                className="border-bottom-0 bg-light"
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
                {secondaryMetricStatistics.map(
                  ({ displayType, branchComparison, value }) => (
                    <TableVisualizationRow
                      key={`${displayType}-${value}`}
                      results={results[branch]}
                      tableLabel={TABLE_LABEL.SECONDARY_METRICS}
                      metricKey={probeSetSlug}
                      {...{ displayType, branchComparison }}
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

export default TableMetricSecondary;
