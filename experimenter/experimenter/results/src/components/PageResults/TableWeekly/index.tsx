/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import TableVisualizationRow from "src/components/PageResults/TableVisualizationRow";
import { ResultsContext } from "src/lib/contexts";
import {
  BRANCH_COMPARISON,
  TABLE_LABEL,
} from "src/lib/visualization/constants";
import {
  AnalysisBases,
  BranchComparisonValues,
  BranchDescription,
  FormattedAnalysisPoint,
} from "src/lib/visualization/types";
import { getTableDisplayType } from "src/lib/visualization/utils";

type TableWeeklyProps = {
  metricKey: string;
  metricName: string;
  group: string;
  branchComparison: BranchComparisonValues;
  analysisBasis?: AnalysisBases;
  segment?: string;
  referenceBranch: string;
};

const getWeekIndexList = (
  metric: string,
  group: string,
  weeklyResults: { [branch: string]: BranchDescription },
  referenceBranch: string,
) => {
  const weekIndexSet = new Set<number>();
  Object.keys(weeklyResults).forEach((branch: string) => {
    if (!(metric in weeklyResults[branch].branch_data[group])) {
      return;
    }

    Object.values(BRANCH_COMPARISON).forEach((branchComparison) => {
      const branchData =
        branchComparison === BRANCH_COMPARISON.ABSOLUTE
          ? weeklyResults[branch].branch_data[group][metric][branchComparison]
              .all
          : weeklyResults[branch].branch_data[group][metric][branchComparison][
              referenceBranch
            ].all;
      branchData.forEach((dataPoint: FormattedAnalysisPoint) => {
        const weekIndex: number =
          "window_index" in dataPoint ? dataPoint["window_index"]! : 0;
        weekIndexSet.add(weekIndex);
      });
    });
  });
  return Array.from(weekIndexSet).sort((a, b) => a - b);
};

const TableWeekly = ({
  metricKey,
  metricName,
  group,
  branchComparison,
  analysisBasis = "enrollments",
  segment = "all",
  referenceBranch,
}: TableWeeklyProps) => {
  const {
    analysis: { weekly },
    sortedBranchNames,
  } = useContext(ResultsContext);
  const weeklyResults = weekly![analysisBasis]![segment]!;
  const weekIndexList = getWeekIndexList(
    metricKey,
    group,
    weeklyResults,
    referenceBranch,
  );
  const tableLabel = TABLE_LABEL.RESULTS;

  return (
    <table
      className="table table-visualization-center"
      data-testid="table-weekly"
    >
      <thead>
        <tr>
          <th scope="col" />
          {weekIndexList.map((weekIndex) => (
            <th key={`${weekIndex}`} scope="col">
              <div>{`Week ${weekIndex}`}</div>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sortedBranchNames.map((branch) => {
          const isReferenceBranch = branch === referenceBranch;
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
              }}
              isControlBranch={isReferenceBranch}
              referenceBranch={referenceBranch}
            />
          );

          return (
            <tr key={`${branch}-${metricKey}`}>
              <th className="align-middle" scope="row">
                {branch}
              </th>
              {/* This case returns the default (baseline) text, and we need the number of
              cells to match the number of weeks */}
              {isReferenceBranch &&
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
