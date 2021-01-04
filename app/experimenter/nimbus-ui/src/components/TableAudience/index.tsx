/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { Table } from "react-bootstrap";
import { useConfig } from "../../hooks";
import { displayConfigLabelOrNotSet } from "../Summary";
import NotSet from "../NotSet";

type TableAudienceProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const TableAudience = ({ experiment }: TableAudienceProps) => {
  const { firefoxMinVersion, channel, targetingConfigSlug } = useConfig();

  return (
    <Table striped bordered data-testid="table-audience" className="mb-4">
      <tbody>
        <tr>
          <th className="w-33">Channel</th>
          <td data-testid="experiment-channel">
            {displayConfigLabelOrNotSet(experiment.channel, channel)}
          </td>
        </tr>
        <tr>
          <th>Minimum version</th>
          <td data-testid="experiment-ff-min">
            {displayConfigLabelOrNotSet(
              experiment.firefoxMinVersion,
              firefoxMinVersion,
            )}
          </td>
        </tr>
        <tr>
          <th>Population %</th>
          <td data-testid="experiment-population">
            {experiment.populationPercent ? (
              `${experiment.populationPercent}%`
            ) : (
              <NotSet />
            )}
          </td>
        </tr>
        {experiment.totalEnrolledClients > 0 && (
          <tr>
            <th>Expected enrolled clients</th>
            <td data-testid="experiment-total-enrolled">
              {experiment.totalEnrolledClients.toLocaleString()}
            </td>
          </tr>
        )}
        {experiment.targetingConfigSlug && (
          <tr>
            <th>Custom audience</th>
            <td data-testid="experiment-target">
              {displayConfigLabelOrNotSet(
                experiment.targetingConfigSlug,
                targetingConfigSlug,
              )}
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableAudience;
