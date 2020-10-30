import React from "react";

import { getTableDisplayType } from "experimenter-rapid/components/experiments/utils";
import { featureOptions } from "experimenter-rapid/components/forms/ExperimentFormOptions";
import {
  METRIC,
  HIGHLIGHTS_METRICS_LIST,
  BRANCH_COMPARISON,
  TABLE_LABEL,
} from "experimenter-rapid/components/visualization/constants/analysis";
import {
  METRICS_TIPS,
  SEGMENT_TIPS,
} from "experimenter-rapid/components/visualization/constants/tooltips";
import ResultsRow from "experimenter-rapid/components/visualization/ResultsRow";
import { ExperimentData } from "experimenter-types/experiment";

const getHighlightMetrics = (
  featureData: Array<string>,
): { value: string; name: string; tooltip: string }[] => {
  const featureNameMappings = featureOptions.reduce((acc, featureRow) => {
    acc[featureRow.value] = featureRow["name"];
    return acc;
  }, {});

  // Make a copy of `HIGHLIGHTS_METRICS_LIST` since we modify it.
  const highlightMetricsList = [...HIGHLIGHTS_METRICS_LIST];
  featureData.forEach((feature) => {
    const featureMetricID = `${feature}_ever_used`;
    highlightMetricsList.unshift({
      value: featureMetricID,
      name: `${featureNameMappings[feature]} conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
    });
  });

  return highlightMetricsList;
};

const HighlightsTable: React.FC<{ experimentData: ExperimentData }> = ({
  experimentData,
}) => {
  const highlightMetricsList = getHighlightMetrics(experimentData.features);
  const resultsData = experimentData.analysis?.overall || {};

  return (
    <table className="table text-left h5 mt-5">
      <tbody>
        {Object.keys(resultsData).map((branch) => {
          const userCountMetric =
            resultsData[branch]["branch_data"][METRIC.USER_COUNT];
          return (
            <tr key={branch}>
              <th className="align-middle" scope="row">
                <p>{branch}</p>
                <p className="h6">
                  {userCountMetric[BRANCH_COMPARISON.ABSOLUTE]["point"]}{" "}
                  participants ({userCountMetric["percent"]}%)
                </p>
              </th>
              <th className="align-middle" scope="row">
                All Users&nbsp;
                <i
                  className="far fa-question-circle"
                  data-tip={SEGMENT_TIPS.ALL_USERS}
                />
              </th>
              <td>
                {highlightMetricsList.map((metric) => {
                  const metricKey = metric.value;
                  const displayType = getTableDisplayType(
                    metricKey,
                    TABLE_LABEL.HIGHLIGHTS,
                    resultsData[branch]["is_control"],
                  );
                  return (
                    <ResultsRow
                      key={metricKey}
                      metricName={metric.name}
                      results={resultsData[branch]}
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

export default HighlightsTable;
