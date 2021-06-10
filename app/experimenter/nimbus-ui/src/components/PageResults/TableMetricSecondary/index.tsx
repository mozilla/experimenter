/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { ReactComponent as Info } from "../../../images/info.svg";
import {
  DISPLAY_TYPE,
  METRIC_TYPE,
  SECONDARY_METRIC_COLUMNS,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import { AnalysisData } from "../../../lib/visualization/types";
import { getExtremeBounds } from "../../../lib/visualization/utils";
import GraphsWeekly from "../GraphsWeekly";
import TableVisualizationRow from "../TableVisualizationRow";
import TooltipWithMarkdown from "../TooltipWithMarkdown";

type SecondaryMetricStatistic = {
  name: string;
  displayType: DISPLAY_TYPE;
  branchComparison?: string;
  value?: string;
};

type TableMetricSecondaryProps = {
  results: AnalysisData;
  outcomeSlug: string;
  outcomeDefaultName: string;
  group: string;
  isDefault?: boolean;
  sortedBranches: string[];
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
  results = {
    daily: [],
    weekly: {},
    overall: {},
    metadata: { metrics: {}, outcomes: {} },
    show_analysis: false,
  },
  outcomeSlug,
  outcomeDefaultName,
  group,
  isDefault = true,
  sortedBranches,
}: TableMetricSecondaryProps) => {
  const secondaryMetricStatistics = getStatistics(outcomeSlug);
  const secondaryType = isDefault
    ? METRIC_TYPE.DEFAULT_SECONDARY
    : METRIC_TYPE.USER_SELECTED_SECONDARY;

  const overallResults = results?.overall!;
  const bounds = getExtremeBounds(
    sortedBranches,
    overallResults,
    outcomeSlug,
    group,
  );
  const outcomeName =
    results.metadata?.metrics[outcomeSlug]?.friendly_name || outcomeDefaultName;
  const outcomeDescription =
    results.metadata?.metrics[outcomeSlug]?.description || undefined;

  return (
    <div data-testid="table-metric-secondary" className="mb-5">
      <h2 className="h5 mb-3" id={outcomeSlug}>
        <div>
          <div className="d-inline-block">
            {outcomeName}{" "}
            {outcomeDescription && (
              <>
                <Info
                  data-tip
                  data-for={outcomeSlug}
                  className="align-baseline"
                />
                <TooltipWithMarkdown
                  tooltipId={outcomeSlug}
                  markdown={outcomeDescription}
                />
              </>
            )}
          </div>
        </div>
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
          {group &&
            sortedBranches.map((branch) => {
              return (
                overallResults[branch].branch_data[group] && (
                  <tr key={`${branch}-${group}`}>
                    <th className="align-middle" scope="row">
                      {branch}
                    </th>
                    {secondaryMetricStatistics.map(
                      ({ displayType, branchComparison, value }) => (
                        <TableVisualizationRow
                          key={`${displayType}-${value}`}
                          results={overallResults[branch]}
                          group={group}
                          tableLabel={TABLE_LABEL.SECONDARY_METRICS}
                          metricKey={outcomeSlug}
                          {...{ displayType, branchComparison, bounds }}
                        />
                      ),
                    )}
                  </tr>
                )
              );
            })}
        </tbody>
      </table>
      {results?.weekly && (
        <GraphsWeekly
          weeklyResults={results.weekly}
          {...{ outcomeSlug, outcomeName }}
          group={group}
        />
      )}
    </div>
  );
};

export default TableMetricSecondary;
