/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { AnalysisData } from "../../lib/visualization/types";
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
  results: AnalysisData["overall"];
  probeSet: getExperiment_experimentBySlug_primaryProbeSets | null;
};

const getStatistics = (
  probeset: string | null,
): Array<PrimaryMetricStatistic> => {
  const probesetMetricID = `${probeset}_ever_used`;

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
  const metricKey = `${probeSet?.slug}_ever_used`;

  return (
    <div data-testid="table-metric-primary">
      <h2 className="h5 mb-3 mt-4">{probeSet?.name}</h2>
      <table className="table text-center mb-5 mt-4">
        <thead>
          <tr>
            <th scope="col" className="border-bottom-0" />
            {PRIMARY_METRIC_COLUMNS.map((value) => (
              <th className="border-bottom-0" key={value.name} scope="col">
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
                {primaryMetricStatistics.map((column) => (
                  <TableVisualizationRow
                    key={column.displayType}
                    branchComparison={column.branchComparison}
                    displayType={column.displayType}
                    results={results[branch]}
                    tableLabel={TABLE_LABEL.PRIMARY_METRICS}
                    {...{ metricKey }}
                  />
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default TableMetricPrimary;
