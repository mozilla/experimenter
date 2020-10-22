import React from "react";

import {
  displaySelectOptionList,
  displaySelectOptionLabels,
} from "experimenter-rapid/components/experiments/utils";
import {
  featureOptions,
  audienceOptions,
  firefoxVersionOptions,
  firefoxChannelOptions,
} from "experimenter-rapid/components/forms/ExperimentFormOptions";
import { ExperimentData } from "experimenter-types/experiment";

const Overview: React.FC<{
  experimentData: ExperimentData;
}> = ({ experimentData }) => {
  const targetingValues = [
    {
      data: experimentData.firefox_min_version,
      options: firefoxVersionOptions,
    },
    { data: experimentData.firefox_channel, options: firefoxChannelOptions },
    { data: experimentData.audience, options: audienceOptions },
  ];
  return (
    <div className="mb-5">
      <table className="table text-left h5 m-0">
        <tbody>
          <tr>
            <th scope="col">
              <p className="text-uppercase">Targeting</p>
              {targetingValues.map((target) => (
                <p key={target.data} className="h6">
                  {displaySelectOptionLabels(target.options, target.data)}
                  {target.data === experimentData.firefox_min_version
                    ? "+"
                    : ""}
                </p>
              ))}
            </th>
            <th scope="col">
              <p className="text-uppercase">Probe Sets</p>
              {displaySelectOptionList(
                featureOptions,
                experimentData.features,
              ).map((feature) => (
                <p key={feature} className="h6">
                  {feature}
                </p>
              ))}
            </th>
            <th scope="col">
              <p className="text-uppercase">Owner</p>
              <p className="h6">{experimentData.owner}</p>
            </th>
          </tr>
        </tbody>
      </table>
      <hr className="mt-0 mb-5" />
    </div>
  );
};

export default Overview;
