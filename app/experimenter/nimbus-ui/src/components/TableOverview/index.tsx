/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { AnalysisData } from "../../lib/visualization/types";
import { useConfig } from "../../hooks";
import { getConfig_nimbusConfig } from "../../types/getConfig";

type TableOverviewProps = {
  experiment: getExperiment_experimentBySlug;
  results: AnalysisData["overall"];
};

type displayConfigOptionsProps =
  | getConfig_nimbusConfig["firefoxMinVersion"]
  | getConfig_nimbusConfig["channels"]
  | getConfig_nimbusConfig["targetingConfigSlug"];

const TableOverview = ({ experiment }: TableOverviewProps) => {
  const { firefoxMinVersion, channels, targetingConfigSlug } = useConfig();

  return (
    <table
      className="table text-left mb-5 border-bottom"
      data-testid="table-overview"
    >
      <tbody>
        <tr>
          <td>
            <h3 className="h6">Targeting</h3>
            <div>
              {displayConfigLabel(
                experiment.firefoxMinVersion,
                firefoxMinVersion,
              )}
              +
            </div>
            <div>
              {experiment.channels?.length
                ? experiment.channels
                    .map((expChannel) =>
                      displayConfigLabel(expChannel, channels),
                    )
                    .join(", ")
                : ""}
            </div>
            <div>
              {displayConfigLabel(
                experiment.targetingConfigSlug,
                targetingConfigSlug,
              )}
            </div>
          </td>
          <td>
            <h3 className="h6">Probe Sets</h3>
            {experiment.primaryProbeSets?.length
              ? experiment.primaryProbeSets.map((probeSet) => (
                  <div key={probeSet?.name}>{probeSet?.name}</div>
                ))
              : ""}
          </td>
          <td>
            <h3 className="h6">Owner</h3>
            <span>{experiment.owner?.email}</span>
          </td>
        </tr>
      </tbody>
    </table>
  );
};

const displayConfigLabel = (
  value: string | null,
  options: displayConfigOptionsProps,
) => {
  return options?.find((obj: any) => obj.value === value)?.label;
};

export default TableOverview;
