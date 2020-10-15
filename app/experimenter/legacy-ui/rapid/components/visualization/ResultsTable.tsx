import React from "react";

import { featureOptions } from "experimenter-rapid/components/forms/ExperimentFormOptions";
import {
  RESULTS_METRICS_LIST,
  TABLE_LABEL,
} from "experimenter-rapid/components/visualization/constants/analysis";
import { METRICS_TIPS } from "experimenter-rapid/components/visualization/constants/tooltips";
import ResultsRow from "experimenter-rapid/components/visualization/ResultsRow";
import { ExperimentData } from "experimenter-types/experiment";

const getResultMetrics = (
  featureData: Array<string>,
): Array<{ value: string; name: string; tooltip: string }> => {
  const featureNameMappings = featureOptions.reduce((acc, featureRow) => {
    acc[featureRow.value] = featureRow["name"];
    return acc;
  }, {});

  // Make a copy of `RESULTS_METRICS_LIST` since we modify it.
  const resultsMetricsList = [...RESULTS_METRICS_LIST];
  featureData.forEach((feature) => {
    const featureMetricID = `${feature}_ever_used`;
    resultsMetricsList.unshift({
      value: featureMetricID,
      name: `${featureNameMappings[feature]} Conversion`,
      tooltip: METRICS_TIPS.CONVERSION,
    });
  });

  return resultsMetricsList;
};

const ResultsTable: React.FC<{ experimentData: ExperimentData }> = ({
  experimentData,
}) => {
  const resultsMetricsList = getResultMetrics(experimentData.features);
  const resultsData = experimentData.analysis?.overall || {};

  return (
    <table className="table text-right h5">
      <thead>
        <tr>
          <th scope="col"></th>
          {resultsMetricsList.map((value, index) => {
            return (
              <th key={index} scope="col">
                {value.name}
                &nbsp;
                <i
                  className="far fa-question-circle"
                  data-tip={value.tooltip}
                />
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        {Object.keys(resultsData).map((branch) => {
          return (
            <tr key={branch}>
              <th className="align-middle" scope="row">
                {branch}
              </th>
              {resultsMetricsList.map((metric) => {
                const metricKey = metric.value;
                return (
                  <ResultsRow
                    key={metricKey}
                    metricKey={metricKey}
                    results={resultsData[branch]}
                    tableLabel={TABLE_LABEL.RESULTS}
                  />
                );
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

export default ResultsTable;
