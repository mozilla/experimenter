/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import { ResultsContext } from "../../../lib/contexts";
import {
  BRANCH_COMPARISON,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import {
  BranchComparisonValues,
  BranchDescription,
  FormattedAnalysisPoint,
} from "../../../lib/visualization/types";
import { getTableDisplayType } from "../../../lib/visualization/utils";
import TableVisualizationRow from "../TableVisualizationRow";

type TableWeeklyProps = {
  metricKey: string;
  metricName: string;
  group: string;
  branchComparison: BranchComparisonValues;
};

const getWeekIndexList = (
  metric: string,
  group: string,
  weeklyResults: { [branch: string]: BranchDescription },
) => {
  const weekIndexSet = new Set();
  Object.keys(weeklyResults).forEach((branch: string) => {
    if (!(metric in weeklyResults[branch].branch_data[group])) {
      return;
    }

    Object.values(BRANCH_COMPARISON).forEach((branchComparison) => {
      const branchData =
        weeklyResults[branch].branch_data[group][metric][branchComparison].all;
      branchData.forEach((dataPoint: FormattedAnalysisPoint) => {
        const weekIndex: number =
          "window_index" in dataPoint ? dataPoint["window_index"]! : 0;
        weekIndexSet.add(weekIndex);
      });
    });
  });
  return Array.from(weekIndexSet).sort();
};

const TableWeekly = ({
  metricKey,
  metricName,
  group,
  branchComparison,
}: TableWeeklyProps) => {
  const {
    analysis: { weekly },
    sortedBranchNames,
    controlBranchName,
  } = useContext(ResultsContext);
  const weeklyResults = weekly!;
  const weekIndexList = getWeekIndexList(metricKey, group, weeklyResults);
  const tableLabel = TABLE_LABEL.RESULTS;

  return (
    <table className="table-visualization-center" data-testid="table-weekly">
      <thead>
        <tr>
          <th scope="col" className="border-bottom-0 bg-light" />
          {weekIndexList.map((weekIndex) => (
            <th
              key={`${weekIndex}`}
              className="border-bottom-0 bg-light"
              scope="col"
            >
              <div>{`Week ${weekIndex}`}</div>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sortedBranchNames.map((branch) => {
          const isControlBranch = branch === controlBranchName;
          const displayType = getTableDisplayType(metricKey, branchComparison);

          const TableRow = () => (
            <TableVisualizationRow
              results={weeklyResults[branch]}
              {...{
                tableLabel,
                group,
                metricName,
                metricKey,
                displayType,
                branchComparison,
                isControlBranch,
              }}
            />
          );

          return (
            <tr key={`${branch}-${metricKey}`}>
              <th className="align-middle" scope="row">
                {branch}
              </th>
              {/* This case returns the default (baseline) text, and we need the number of
              cells to match the number of weeks */}
              {isControlBranch &&
              branchComparison === BRANCH_COMPARISON.UPLIFT ? (
                weekIndexList.map((weekIndex) => (
                  <TableRow key={`${displayType}-${metricKey}-${weekIndex}}`} />
                ))
              ) : (
                <TableRow key={`${displayType}-${metricKey}`} />
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default TableWeekly;
