/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import GraphsWeekly from "src/components/PageResults/GraphsWeekly";
import MetricHeader from "src/components/PageResults/TableMetricCount/MetricHeader";
import TableVisualizationRow from "src/components/PageResults/TableVisualizationRow";
import { ResultsContext } from "src/lib/contexts";
import {
  COUNT_METRIC_COLUMNS,
  DISPLAY_TYPE,
  METRIC_TYPE,
  TABLE_LABEL,
} from "src/lib/visualization/constants";
import {
  AnalysisBases,
  BranchComparisonValues,
} from "src/lib/visualization/types";
import { getExtremeBounds } from "src/lib/visualization/utils";

type CountMetricStatistic = {
  name: string;
  displayType: DISPLAY_TYPE;
  branchComparison: BranchComparisonValues;
  value?: string;
};

type MetricTypes =
  | typeof METRIC_TYPE.PRIMARY
  | typeof METRIC_TYPE.USER_SELECTED_SECONDARY
  | typeof METRIC_TYPE.DEFAULT_SECONDARY
  | typeof METRIC_TYPE.GUARDRAIL;

type TableMetricCountProps = {
  outcomeSlug: string;
  outcomeDefaultName: string;
  group: string;
  metricType?: MetricTypes;
  analysisBasis?: AnalysisBases;
  segment?: string;
  referenceBranch: string;
};

const getStatistics = (slug: string): Array<CountMetricStatistic> => {
  // Make a copy of `COUNT_METRIC_COLUMNS` since we modify it.
  const countMetricStatisticsList = COUNT_METRIC_COLUMNS.map(
    (statistic: CountMetricStatistic) => {
      statistic["value"] = slug;
      return statistic;
    },
  );

  return countMetricStatisticsList;
};

const TableMetricCount = ({
  outcomeSlug,
  outcomeDefaultName,
  group,
  metricType = METRIC_TYPE.DEFAULT_SECONDARY,
  analysisBasis = "enrollments",
  segment = "all",
  referenceBranch,
}: TableMetricCountProps) => {
  const countMetricStatistics = getStatistics(outcomeSlug);
  const {
    analysis: { metadata, overall, weekly },
    sortedBranchNames,
  } = useContext(ResultsContext);
  const overallResults = overall![analysisBasis]?.[segment]!;
  const weeklyBasis = weekly![analysisBasis];

  const bounds = getExtremeBounds(
    sortedBranchNames,
    overall![analysisBasis]!,
    outcomeSlug,
    group,
    segment,
    referenceBranch,
  );
  const outcomeName =
    metadata?.metrics[outcomeSlug]?.friendly_name || outcomeDefaultName;

  return (
    <div data-testid="table-metric-secondary" className="mb-5">
      <MetricHeader
        outcomeSlug={outcomeSlug}
        outcomeDefaultName={outcomeDefaultName}
        metricType={metricType}
      />

      <table className="table table-visualization-center border">
        <thead>
          <tr>
            <th scope="col" />
            {COUNT_METRIC_COLUMNS.map((value) => (
              <th key={value.name} scope="col">
                <div>{value.name}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {group &&
            sortedBranchNames.map((branch) => {
              const isReferenceBranch = branch === referenceBranch;
              return (
                overallResults[branch].branch_data[group] && (
                  <tr key={`${branch}-${group}`}>
                    <th className="align-middle" scope="row">
                      {branch}
                    </th>
                    {countMetricStatistics.map(
                      ({ displayType, value, branchComparison }) => (
                        <TableVisualizationRow
                          key={`${displayType}-${value}`}
                          results={overallResults[branch]}
                          tableLabel={TABLE_LABEL.SECONDARY_METRICS}
                          metricKey={outcomeSlug}
                          {...{
                            displayType,
                            branchComparison,
                            bounds,
                            group,
                          }}
                          isControlBranch={isReferenceBranch}
                          referenceBranch={referenceBranch}
                        />
                      ),
                    )}
                  </tr>
                )
              );
            })}
        </tbody>
      </table>
      {weeklyBasis?.all && (
        <GraphsWeekly
          weeklyResults={weeklyBasis}
          referenceBranch={referenceBranch}
          {...{ outcomeSlug, outcomeName, group }}
        />
      )}
    </div>
  );
};

export default TableMetricCount;
