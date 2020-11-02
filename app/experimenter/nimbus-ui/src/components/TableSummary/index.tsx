/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { Table } from "react-bootstrap";
import { useConfig } from "../../hooks";
import { getConfig_nimbusConfig } from "../../types/getConfig";

type TableSummaryProps = {
  experiment: getExperiment_experimentBySlug;
};

const TableSummary = ({ experiment }: TableSummaryProps) => {
  const { firefoxMinVersion, channels, targetingConfigSlug } = useConfig();

  return (
    <Table striped bordered className="mt-5" data-testid="table-summary">
      <tbody>
        <tr>
          <th className="font-weight-bold">Experiment Owner</th>
          <td data-testid="experiment-owner">
            {experiment.owner?.email ? experiment.owner.email : notSet("Owner")}
          </td>
        </tr>
        <tr>
          <th className="font-weight-bold">
            <b>Hypothesis</b>
          </th>
          <td data-testid="experiment-hypothesis">
            {experiment.hypothesis
              ? experiment.hypothesis
              : notSet("Hypothesis")}
          </td>
        </tr>
        <tr>
          <th className="font-weight-bold">Probe Sets</th>
          <td>
            <span data-testid="experiment-probe-primary" className="d-block">
              Primary:{" "}
              {experiment.primaryProbeSets?.length
                ? experiment.primaryProbeSets
                    .map((probeSet) => probeSet?.name)
                    .join(", ")
                : notSet("probe")}
            </span>
            <span data-testid="experiment-probe-secondary">
              Secondary:{" "}
              {experiment.secondaryProbeSets?.length
                ? experiment.secondaryProbeSets
                    .map((probeSet) => probeSet?.name)
                    .join(", ")
                : notSet("probe")}
            </span>
          </td>
        </tr>
        <tr>
          <th className="font-weight-bold">Audience</th>
          <td>
            <span data-testid="experiment-target">
              {displayConfigLabelOrNotSet(
                "Target audience",
                experiment.targetingConfigSlug,
                targetingConfigSlug,
              )}
              ,{" "}
            </span>
            <span data-testid="experiment-channels">
              {experiment.channels?.length
                ? experiment.channels
                    .map((expChannel) =>
                      displayConfigLabelOrNotSet(
                        "channel",
                        expChannel,
                        channels,
                      ),
                    )
                    .join(", ")
                : notSet("channel")}
              {", "}
            </span>
            <span data-testid="experiment-ff-min">
              {displayConfigLabelOrNotSet(
                "Firefox minimum version",
                experiment.firefoxMinVersion,
                firefoxMinVersion,
              )}
            </span>
            <span className="d-block">
              <span data-testid="experiment-population">
                {experiment.populationPercent
                  ? `${experiment.populationPercent}% of population`
                  : notSet("Population percentage")}
              </span>
              <span data-testid="experiment-total-enrolled">
                {" "}
                totalling{" "}
                {experiment.totalEnrolledClients
                  ? `${experiment.totalEnrolledClients.toLocaleString()} expected enrolled clients`
                  : notSet("expected enrolled clients")}
              </span>
            </span>
          </td>
        </tr>
        <tr>
          <th className="font-weight-bold">Duration</th>
          <td>
            <span data-testid="experiment-duration">
              {displayDaysOrNotSet(
                "Proposed duration",
                experiment.proposedDuration,
              )}{" "}
            </span>
            <span data-testid="experiment-enrollment">
              over an enrollment period of{" "}
              {displayDaysOrNotSet(
                "proposed enrollment",
                experiment.proposedEnrollment,
              )}
            </span>
          </td>
        </tr>
      </tbody>
    </Table>
  );
};

type displayConfigOptionsProps =
  | getConfig_nimbusConfig["firefoxMinVersion"]
  | getConfig_nimbusConfig["channels"]
  | getConfig_nimbusConfig["targetingConfigSlug"];

const displayConfigLabelOrNotSet = (
  description: string,
  value: string | null,
  options: displayConfigOptionsProps,
) => {
  if (!value) return notSet(description);
  const label = options?.find((obj: any) => obj.value === value)?.label;
  return label;
};

const displayDaysOrNotSet = (
  description: string,
  numberOfDays: number | null,
) => {
  if (!numberOfDays) return notSet(description);
  if (numberOfDays === 1) {
    return `${numberOfDays} day`;
  } else {
    return `${numberOfDays} days`;
  }
};

const notSet = (description: string) => (
  <span className="text-danger">{`${description} not set`}</span>
);

export default TableSummary;
