/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import { ReactComponent as Info } from "../../../images/info.svg";
import { AnalysisContext, ExperimentContext } from "../../../lib/contexts";
import {
  BRANCH_COMPARISON,
  HIGHLIGHTS_METRICS_LIST,
  METRIC,
  METRICS_TIPS,
  SEGMENT_TIPS,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import { getTableDisplayType } from "../../../lib/visualization/utils";
import { getExperiment_experimentBySlug_primaryProbeSets } from "../../../types/getExperiment";
import TableVisualizationRow from "../TableVisualizationRow";

const getHighlightMetrics = (
  probeSets: (getExperiment_experimentBySlug_primaryProbeSets | null)[],
) => {
  // Make a copy of `HIGHLIGHTS_METRICS_LIST` since we modify it.
  const highlightMetricsList = [...HIGHLIGHTS_METRICS_LIST];
  probeSets.forEach((probeSet) => {
    highlightMetricsList.unshift({
      value: `${probeSet!.slug}_ever_used`,
      name: `${probeSet!.name} conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
    });
  });

  return highlightMetricsList;
};

const TableHighlights = () => {
  const primaryProbeSets = useContext(ExperimentContext).experiment!
    .primaryProbeSets!;
  const results = useContext(AnalysisContext).analysis!.overall!;

  const highlightMetricsList = getHighlightMetrics(primaryProbeSets);

  return (
    <table data-testid="table-highlights" className="table mt-4 mb-0">
      <tbody>
        {Object.keys(results).map((branch) => {
          const userCountMetric =
            results[branch]["branch_data"][METRIC.USER_COUNT];
          const participantCount =
            userCountMetric[BRANCH_COMPARISON.ABSOLUTE]["first"]["point"];
          return (
            <tr key={branch} className="border-top">
              <th className="align-middle p-1 p-lg-3" scope="row">
                <p>{branch}</p>
                <p className="h6">
                  {participantCount} participants ({userCountMetric["percent"]}
                  %)
                </p>
              </th>
              <td className="p-1 p-lg-3 align-middle">
                <span className="align-middle">All Users&nbsp;</span>
                <Info data-tip={SEGMENT_TIPS.ALL_USERS} />
              </td>
              <td className="pt-3 px-3 pb-0">
                {highlightMetricsList.map((metric) => {
                  const metricKey = metric.value;
                  const displayType = getTableDisplayType(
                    metricKey,
                    TABLE_LABEL.HIGHLIGHTS,
                    results[branch]["is_control"],
                  );
                  return (
                    <TableVisualizationRow
                      key={`${displayType}-${metricKey}`}
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
