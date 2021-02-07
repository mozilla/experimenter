/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import { Table } from "react-bootstrap";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig } from "../../../hooks";
import { ExperimentContext } from "../../../lib/contexts";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import NotSet from "../../NotSet";

type TableAudienceProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const TableAudience = () => {
  const {
    firefoxMinVersion: configFirefoxMinVersion,
    channel: configChannels,
    targetingConfigSlug: configTargetingConfigSlug,
  } = useConfig();
  const { experiment } = useContext(ExperimentContext);
  const {
    channel,
    firefoxMinVersion,
    populationPercent,
    totalEnrolledClients,
    targetingConfigSlug,
    targetingConfigTargeting,
  } = experiment!;

  return (
    <Table striped bordered data-testid="table-audience" className="mb-4">
      <tbody>
        <tr>
          <th className="w-33">Channel</th>
          <td data-testid="experiment-channel">
            {displayConfigLabelOrNotSet(channel, configChannels)}
          </td>
        </tr>
        <tr>
          <th>Minimum version</th>
          <td data-testid="experiment-ff-min">
            {displayConfigLabelOrNotSet(
              firefoxMinVersion,
              configFirefoxMinVersion,
            )}
          </td>
        </tr>
        <tr>
          <th>Population %</th>
          <td data-testid="experiment-population">
            {populationPercent ? `${populationPercent}%` : <NotSet />}
          </td>
        </tr>
        {totalEnrolledClients > 0 && (
          <tr>
            <th>Expected enrolled clients</th>
            <td data-testid="experiment-total-enrolled">
              {totalEnrolledClients.toLocaleString()}
            </td>
          </tr>
        )}
        {targetingConfigSlug && (
          <tr>
            <th>Custom audience</th>
            <td data-testid="experiment-target">
              {displayConfigLabelOrNotSet(
                targetingConfigSlug,
                configTargetingConfigSlug,
              )}
            </td>
          </tr>
        )}
        {targetingConfigTargeting !== "" && (
          <tr>
            <th>Full targeting expression</th>
            <td
              data-testid="experiment-target-expression"
              className="text-monospace"
            >
              {targetingConfigTargeting}
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableAudience;
