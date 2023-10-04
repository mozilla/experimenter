/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import TableVisualizationRow from "src/components/PageResults/TableVisualizationRow";
import { useOutcomes } from "src/hooks";
import { ResultsContext } from "src/lib/contexts";
import { OutcomesList } from "src/lib/types";
import {
  BRANCH_COMPARISON,
  GROUP,
  HIGHLIGHTS_METRICS_LIST,
  METRIC,
  METRICS_TIPS,
  METRIC_TO_GROUP,
  TABLE_LABEL,
} from "src/lib/visualization/constants";
import {
  AnalysisBases,
  BranchComparisonValues,
} from "src/lib/visualization/types";
import { getTableDisplayType } from "src/lib/visualization/utils";
import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_referenceBranch,
  getExperiment_experimentBySlug_treatmentBranches,
} from "src/types/getExperiment";
import { NimbusExperimentApplicationEnum } from "src/types/globalTypes";

export type TableHighlightsProps = {
  experiment: getExperiment_experimentBySlug;
  branchComparison?: BranchComparisonValues;
  analysisBasis?: AnalysisBases;
  segment?: string;
};

type Branch =
  | getExperiment_experimentBySlug_referenceBranch
  | getExperiment_experimentBySlug_treatmentBranches;

const getHighlightMetrics = (outcomes: OutcomesList, isDesktop = false) => {
  // Make a copy of `HIGHLIGHTS_METRICS_LIST` since we modify it.
  const highlightMetricsList = HIGHLIGHTS_METRICS_LIST.map(
    (highlightMetric) => {
      if (isDesktop && highlightMetric.value === METRIC.DAYS_OF_USE) {
        return {
          value: METRIC.QUALIFIED_CUMULATIVE_DAYS_OF_USE,
          name: "Qualified Cumulative Days of Use",
          tooltip: METRICS_TIPS.QUALIFIED_CUMULATIVE_DAYS_OF_USE,
          group: METRIC_TO_GROUP[METRIC.QUALIFIED_CUMULATIVE_DAYS_OF_USE],
        };
      }
      return highlightMetric;
    },
  );
  outcomes?.forEach((outcome) => {
    if (!outcome?.isDefault) {
      return;
    }
    highlightMetricsList.unshift({
      value: `${outcome!.slug}_ever_used`,
      name: `${outcome!.friendlyName} conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
      group: GROUP.OTHER,
    });
  });

  return highlightMetricsList;
};

const getBranchDescriptions = (
  control: Branch | null,
  treatments: (Branch | null)[] | null,
) => {
  const branches = [control, ...(treatments || [])].filter(
    (branch): branch is Branch => branch !== null,
  );

  return branches.reduce(
    (descriptionsMap: { [branchSlug: string]: string }, branch: Branch) => {
      descriptionsMap[branch!.slug] = branch?.description;
      return descriptionsMap;
    },
    {},
  );
};

const TableHighlights = ({
  experiment,
  branchComparison = BRANCH_COMPARISON.UPLIFT,
  analysisBasis = "enrollments",
  segment = "all",
}: TableHighlightsProps) => {
  const { primaryOutcomes } = useOutcomes(experiment);
  const highlightMetricsList = getHighlightMetrics(
    primaryOutcomes,
    experiment.application === NimbusExperimentApplicationEnum.DESKTOP,
  );
  const branchDescriptions = getBranchDescriptions(
    experiment.referenceBranch,
    experiment.treatmentBranches,
  );
  const {
    analysis: { metadata, overall },
    sortedBranchNames,
    controlBranchName,
  } = useContext(ResultsContext);
  const overallResults = overall![analysisBasis]?.[segment]!;

  return (
    <table data-testid="table-highlights" className="table mb-0 pt-2">
      <tbody>
        {sortedBranchNames.map((branch) => {
          const userCountMetric =
            overallResults[branch]["branch_data"][GROUP.OTHER][
              METRIC.USER_COUNT
            ];
          const participantCount =
            userCountMetric[BRANCH_COMPARISON.ABSOLUTE]["first"]["point"];
          const isControlBranch = branch === controlBranchName;

          return (
            <tr key={branch} className="border-top">
              <th className="align-middle p-3" scope="row">
                <p>{branch}</p>
                <p className="h6">
                  {participantCount} participants ({userCountMetric["percent"]}
                  %)
                </p>
              </th>
              <td className="p-3 col-md-4 align-middle">
                {branchDescriptions[branch]}
              </td>
              {isControlBranch &&
              branchComparison === BRANCH_COMPARISON.UPLIFT ? (
                <td className="p-3 align-middle">
                  <div className="font-italic align-middle">---baseline---</div>
                </td>
              ) : (
                <td className="pt-3 px-3">
                  {highlightMetricsList.map((metric) => {
                    const metricKey = metric.value;
                    const displayType = getTableDisplayType(
                      metricKey,
                      branchComparison,
                    );
                    const tooltip =
                      metadata?.metrics[metricKey]?.description ||
                      metric.tooltip;
                    return (
                      <TableVisualizationRow
                        key={`${displayType}-${metricKey}`}
                        metricName={metric.name}
                        results={overallResults[branch]}
                        group={metric.group}
                        tableLabel={TABLE_LABEL.HIGHLIGHTS}
                        {...{
                          metricKey,
                          displayType,
                          tooltip,
                          isControlBranch,
                          branchComparison,
                        }}
                      />
                    );
                  })}
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default TableHighlights;
