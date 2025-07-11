/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import TableVisualizationRow from "src/components/PageResults/TableVisualizationRow";
import { ResultsContext } from "src/lib/contexts";
import {
  CONVERSION_METRIC_COLUMNS,
  DISPLAY_TYPE,
  GROUP,
  TABLE_LABEL,
} from "src/lib/visualization/constants";
import {
  AnalysisBases,
  BranchComparisonValues,
} from "src/lib/visualization/types";
import { getExtremeBounds } from "src/lib/visualization/utils";
import { getConfig_nimbusConfig_outcomes } from "src/types/getConfig";

type ConversionMetricStatistic = {
  name: string;
  displayType: DISPLAY_TYPE;
  branchComparison: BranchComparisonValues;
  value?: string;
};

type TableMetricConversionProps = {
  outcome: getConfig_nimbusConfig_outcomes;
  analysisBasis?: AnalysisBases;
  segment?: string;
  referenceBranch: string;
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
  outcome,
  analysisBasis = "enrollments",
  segment = "all",
  referenceBranch,
}: TableMetricConversionProps) => {
  const {
    analysis: { overall },
    sortedBranchNames,
  } = useContext(ResultsContext);
  const overallResults = overall![analysisBasis]?.[segment]!;
  const conversionMetricStatistics = getStatistics(outcome.slug!);
  const metricKey = `${outcome.slug}_ever_used`;
  const bounds = getExtremeBounds(
    sortedBranchNames,
    overall![analysisBasis]!,
    outcome.slug!,
    GROUP.OTHER,
    segment,
    referenceBranch,
  );

  return (
    <div data-testid="table-metric-primary" className="mb-5">
      <h3 className="h6 mb-3" id={outcome.slug!}>
        {outcome.friendlyName}
      </h3>
      <table className="table table-visualization-center border">
        <thead>
          <tr>
            <th scope="col" />
            {CONVERSION_METRIC_COLUMNS.map((value) => (
              <th key={value.name} scope="col">
                <div>{value.name}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.keys(overallResults).map((branch) => {
            const isReferenceBranch = branch === referenceBranch;
            return (
              <tr key={branch}>
                <th className="align-middle" scope="row">
                  {branch}
                </th>
                {conversionMetricStatistics.map(
                  ({ displayType, value, branchComparison }) => (
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
                      }}
                      isControlBranch={isReferenceBranch}
                      referenceBranch={referenceBranch}
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
