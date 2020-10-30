import React from "react";

import { displaySelectOptionList } from "experimenter-rapid/components/experiments/utils";
import { featureOptions } from "experimenter-rapid/components/forms/ExperimentFormOptions";
import {
  PRIMARY_METRIC_COLUMNS,
  TABLE_LABEL,
  DISPLAY_TYPE,
} from "experimenter-rapid/components/visualization/constants/analysis";
import ResultsRow from "experimenter-rapid/components/visualization/ResultsRow";
import { ExperimentData } from "experimenter-types/experiment";

const getStatistics = (
  probeset: string,
): Array<{
  name: string;
  displayType: DISPLAY_TYPE;
  branchComparison?: string;
}> => {
  const probesetMetricID = `${probeset}_ever_used`;

  // Make a copy of `PRIMARY_METRIC_COLUMNS` since we modify it.
  const primaryMetricStatisticsList = PRIMARY_METRIC_COLUMNS.map(
    (statistic) => {
      statistic["value"] = probesetMetricID;
      return statistic;
    },
  );

  return primaryMetricStatisticsList;
};

const PrimaryMetrics: React.FC<{
  experimentData: ExperimentData;
  probeset: string;
}> = ({ experimentData, probeset }) => {
  const probesetDisplayName = displaySelectOptionList(
    featureOptions,
    probeset,
  ).pop();
  const statsData = experimentData.analysis?.overall || {};
  const primaryMetricStatistics = getStatistics(probeset);
  const metricKey = `${probeset}_ever_used`;

  return (
    <div>
      <h2 className="font-weight-bold">{probesetDisplayName}</h2>
      <table className="table text-right h5 mb-5">
        <thead>
          <tr>
            <th scope="col"></th>
            {PRIMARY_METRIC_COLUMNS.map((value) => (
              <th key={value.name} scope="col">
                <div>{value.name}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.keys(statsData).map((branch) => {
            return (
              <tr key={branch}>
                <th className="align-middle" scope="row">
                  {branch}
                </th>
                {primaryMetricStatistics.map((column) => (
                  <ResultsRow
                    key={column.displayType}
                    branchComparison={column.branchComparison}
                    displayType={column.displayType}
                    results={statsData[branch]}
                    tableLabel={TABLE_LABEL.PRIMARY_METRICS}
                    {...{ metricKey }}
                  />
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default PrimaryMetrics;
