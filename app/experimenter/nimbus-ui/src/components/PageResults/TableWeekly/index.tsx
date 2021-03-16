/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  BRANCH_COMPARISON,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import {
  AnalysisDataWeekly,
  BranchDescription,
  FormattedAnalysisPoint,
} from "../../../lib/visualization/types";
import { getTableDisplayType } from "../../../lib/visualization/utils";
import TableVisualizationRow from "../TableVisualizationRow";

type TableWeeklyProps = {
  metricKey: string;
  metricName: string;
  results: AnalysisDataWeekly;
};

const getWeekCount = (
  metric: string,
  weeklyResults: { [branch: string]: BranchDescription },
) => {
  let maxWeeks = 0;
  Object.keys(weeklyResults).forEach((branch: string) => {
    if (!(metric in weeklyResults[branch].branch_data)) {
      return;
    }
    Object.values(BRANCH_COMPARISON).forEach((branchComparison) => {
      const branchData =
        weeklyResults[branch].branch_data[metric][branchComparison].all;
      branchData.forEach((dataPoint: FormattedAnalysisPoint) => {
        const weekIndex: number =
          "window_index" in dataPoint ? dataPoint["window_index"]! : 0;
        if (weekIndex > maxWeeks) {
          maxWeeks = weekIndex;
        }
      });
    });
  });
  return maxWeeks;
};

const TableWeekly = ({
  metricKey,
  metricName,
  results = {},
}: TableWeeklyProps) => {
  const weekCount = getWeekCount(metricKey, results);

  return (
    <table
      className="table-visualization-center mb-5"
      data-testid="table-weekly"
    >
      <thead>
        <tr>
          <th scope="col" className="border-bottom-0 bg-light" />
          {Array.from({ length: weekCount }).map((x, weekIndex) => (
            <th
              key={weekIndex}
              className="border-bottom-0 bg-light"
              scope="col"
            >
              <div>{`Week ${weekIndex + 1}`}</div>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Object.keys(results).map((branch) => {
          const displayType = getTableDisplayType(
            metricKey,
            TABLE_LABEL.RESULTS,
            results[branch]["is_control"],
          );

          return (
            <tr key={`${branch}-${metricKey}`}>
              <th className="align-middle" scope="row">
                {branch}
              </th>
              <TableVisualizationRow
                key={`${displayType}-${metricKey}`}
                metricName={metricName}
                results={results[branch]}
                tableLabel={TABLE_LABEL.RESULTS}
                {...{ metricKey }}
                {...{ displayType }}
                window="weekly"
              />
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default TableWeekly;
