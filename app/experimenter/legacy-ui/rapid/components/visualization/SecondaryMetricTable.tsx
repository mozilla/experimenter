import React from "react";

import {
  SECONDARY_METRIC_COLUMNS,
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
  // Make a copy of `SECONDARY_METRIC_COLUMNS` since we modify it.
  const secondaryMetricStatisticsList = SECONDARY_METRIC_COLUMNS.map(
    (statistic) => {
      statistic["value"] = probeset;
      return statistic;
    },
  );

  return secondaryMetricStatisticsList;
};

const SecondaryMetrics: React.FC<{
  experimentData: ExperimentData;
  probeset: string;
}> = ({ experimentData, probeset }) => {
  const statsData = experimentData.analysis?.overall || {};
  const secondaryMetricStatistics = getStatistics(probeset);

  return (
    <div>
      <h2 className="font-weight-bold">{probeset}</h2>
      <table className="table text-right h5 mb-5">
        <thead>
          <tr>
            <th scope="col"></th>
            {SECONDARY_METRIC_COLUMNS.map((value) => (
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
                {secondaryMetricStatistics.map((column) => (
                  <ResultsRow
                    key={column.displayType}
                    branchComparison={column.branchComparison}
                    displayType={column.displayType}
                    metricKey={probeset}
                    results={statsData[branch]}
                    tableLabel={TABLE_LABEL.PRIMARY_METRICS}
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

export default SecondaryMetrics;
