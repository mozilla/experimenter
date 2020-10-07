import React from "react";

import { featureOptions } from "experimenter-rapid/components/forms/ExperimentFormOptions";
import {
  SIGNIFICANCE,
  METRIC,
  RESULTS_METRICS_LIST,
  BRANCH_COMPARISON,
  STATISTIC,
} from "experimenter-rapid/components/visualization/constants/analysis";
import { RESULT_COLUMN_TIPS } from "experimenter-rapid/components/visualization/constants/tooltips";
import ResultsRow from "experimenter-rapid/components/visualization/ResultsRow";
import { AnalysisPoint, ExperimentData } from "experimenter-types/experiment";

const getResultMetrics = (
  featureData: Array<string>,
): Array<{ value: string; name: string; tooltip: string }> => {
  const featureNameMappings = featureOptions.reduce((acc, featureRow) => {
    acc[featureRow.value] = featureRow["name"];
    return acc;
  }, {});
  const resultsMetricsList = [...RESULTS_METRICS_LIST];
  featureData.forEach((feature) => {
    const featureMetricID = `${feature}_ever_used`;
    resultsMetricsList.unshift({
      value: featureMetricID,
      name: `${featureNameMappings[feature]} Conversion`,
      tooltip: RESULT_COLUMN_TIPS.CONVERSION,
    });
  });

  return resultsMetricsList;
};

const computeSignificance = (lower: number, upper: number): SIGNIFICANCE => {
  if (lower < 0 && upper < 0) {
    return SIGNIFICANCE.NEGATIVE;
  } else if (lower > 0 && upper > 0) {
    return SIGNIFICANCE.POSITIVE;
  } else {
    return SIGNIFICANCE.NEUTRAL;
  }
};

const getResultsData = (data: ExperimentData) => {
  const analysisData = data.analysis;
  if (!analysisData) {
    return {};
  }

  const resultMetrics = analysisData["result_map"] || [];
  const fullResultsData = analysisData["overall"];

  const results = {};
  Object.values(fullResultsData).forEach((row: AnalysisPoint) => {
    const { metric, branch, statistic, point, lower, upper, comparison } = row;
    results[branch] = results[branch] || {};

    // `comparison` could be empty, `difference`, or `relative_uplift`.
    // Here we want to display the empty comparison which means a given
    // branch's values is not relative to another branch. We also want
    // to use the `difference` comparison to decide whether there was
    // any positive or negative significance.
    if (metric in resultMetrics && resultMetrics[metric] === statistic) {
      results[branch][metric] = results[branch][metric] || {};

      let newData = {};
      if (!comparison) {
        newData = { lower, upper, point };
      }

      if (comparison === BRANCH_COMPARISON.DIFFERENCE && lower && upper) {
        newData = { significance: computeSignificance(lower, upper) };
      }

      Object.assign(results[branch][metric], newData);
    }

    if (metric === METRIC.USER_COUNT && statistic === STATISTIC.PERCENT) {
      results[branch][METRIC.USER_COUNT]["percent"] = point;
    }
  });

  return results;
};

const ResultsTable: React.FC<{ experimentData: ExperimentData }> = ({
  experimentData,
}) => {
  const resultsMetricsList = getResultMetrics(experimentData.features);
  const resultsData = getResultsData(experimentData);

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
