/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { AnalysisData } from "../../lib/visualization/types";
import {
  HIGHLIGHTS_METRICS_LIST,
  METRICS_TIPS,
  METRIC,
  BRANCH_COMPARISON,
  SEGMENT_TIPS,
  TABLE_LABEL,
} from "../../lib/visualization/constants";
import { getTableDisplayType } from "../../lib/visualization/utils";
import { getExperiment_experimentBySlug_primaryProbeSets } from "../../types/getExperiment";
import TableVisualizationRow from "../TableVisualizationRow";
import { ReactComponent as Info } from "../../images/info.svg";

type TableHighlightsProps = {
  primaryProbeSets: (getExperiment_experimentBySlug_primaryProbeSets | null)[];
  results: AnalysisData["overall"];
};

const getHighlightMetrics = (
  probeSets: (getExperiment_experimentBySlug_primaryProbeSets | null)[],
) => {
  // Make a copy of `HIGHLIGHTS_METRICS_LIST` since we modify it.
  const highlightMetricsList = [...HIGHLIGHTS_METRICS_LIST];
  probeSets.forEach((probeSet) => {
    highlightMetricsList.unshift({
      value: `${probeSet!.slug.replace(/-/g, "_")}_ever_used`,
      name: `${probeSet!.name} conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
    });
  });

  return highlightMetricsList;
};

const TableHighlights = ({
  primaryProbeSets,
  results = {},
}: TableHighlightsProps) => {
  const highlightMetricsList = getHighlightMetrics(primaryProbeSets);

  return (
    <table data-testid="table-highlights" className="mt-4">
      <tbody>
        {Object.keys(results).map((branch) => {
          const userCountMetric =
            results[branch]["branch_data"][METRIC.USER_COUNT];
          return (
            <tr key={branch} className="border-top">
              <th className="align-middle p-1 p-lg-3" scope="row">
                <p>{branch}</p>
                <p className="h6">
                  {userCountMetric[BRANCH_COMPARISON.ABSOLUTE]["point"]}{" "}
                  participants ({userCountMetric["percent"]}%)
                </p>
              </th>
              <td className="p-1 p-lg-3">
                <span className="align-middle">All Users&nbsp;</span>
                <Info data-tip={SEGMENT_TIPS.ALL_USERS} />
              </td>
              <td className="pt-1 px-1 pt-lg-3 px-lg-3">
                {highlightMetricsList.map((metric) => {
                  const metricKey = metric.value;
                  const displayType = getTableDisplayType(
                    metricKey,
                    TABLE_LABEL.HIGHLIGHTS,
                    results[branch]["is_control"],
                  );
                  return (
                    <TableVisualizationRow
                      key={metricKey}
                      metricName={metric.name}
                      results={results[branch]}
                      tableLabel={TABLE_LABEL.HIGHLIGHTS}
                      {...{ metricKey, displayType }}
                    />
                  );
                })}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default TableHighlights;
