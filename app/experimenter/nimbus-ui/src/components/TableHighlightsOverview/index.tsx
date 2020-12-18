/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { AnalysisData } from "../../lib/visualization/types";
import { useConfig } from "../../hooks";
import { getConfigLabel } from "../../lib/getConfigLabel";

type TableHighlightsOverviewProps = {
  experiment: getExperiment_experimentBySlug;
  results: AnalysisData["overall"];
};

const TableHighlightsOverview = ({
  experiment,
}: TableHighlightsOverviewProps) => {
  const { firefoxMinVersion, channel, targetingConfigSlug } = useConfig();

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
              {getConfigLabel(experiment.firefoxMinVersion, firefoxMinVersion)}+
            </div>
            <div>{getConfigLabel(experiment.channel, channel)}</div>
            <div>
              {getConfigLabel(
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

export default TableHighlightsOverview;
