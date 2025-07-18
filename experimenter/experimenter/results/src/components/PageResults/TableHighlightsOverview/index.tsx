/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { useConfig, useOutcomes } from "src/hooks";
import { getConfigLabel } from "src/lib/getConfigLabel";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

type TableHighlightsOverviewProps = {
  experiment: getExperiment_experimentBySlug;
};

const TableHighlightsOverview = ({
  experiment,
}: TableHighlightsOverviewProps) => {
  const { firefoxVersions, channels, targetingConfigs } = useConfig();
  const { primaryOutcomes } = useOutcomes(experiment);

  return (
    <div className="mb-5">
      <table
        className="table border-1 text-left"
        data-testid="table-highlights-overview"
      >
        <tbody>
          <tr>
            <td className="p-3">
              <h3 className="h6">Targeting</h3>
              <div>
                Minimum{" "}
                {getConfigLabel(experiment.firefoxMinVersion, firefoxVersions)}+
              </div>
              <div>
                Maximum{" "}
                {getConfigLabel(experiment.firefoxMaxVersion, firefoxVersions)}+
              </div>
              <div>{getConfigLabel(experiment.channel, channels)}</div>
              <div>
                {getConfigLabel(
                  experiment.targetingConfigSlug,
                  targetingConfigs,
                )}
              </div>
            </td>
            <td className="p-3">
              <h3 className="h6">Outcomes</h3>
              {primaryOutcomes.length > 0 &&
                primaryOutcomes.map((outcome) => (
                  <div key={outcome!.slug!}>{outcome?.friendlyName}</div>
                ))}
            </td>
            <td className="p-3">
              <h3 className="h6">Owner</h3>
              <span>{experiment.owner?.email}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default TableHighlightsOverview;
