/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import { useConfig } from "../../../hooks";
import { ExperimentContext } from "../../../lib/contexts";
import { getConfigLabel } from "../../../lib/getConfigLabel";

const TableHighlightsOverview = () => {
  const { experiment } = useContext(ExperimentContext);
  const {
    firefoxMinVersion,
    channel,
    targetingConfigSlug,
    primaryProbeSets,
    owner,
  } = experiment!;

  const {
    firefoxMinVersion: configFirefoxMinVersions,
    channel: configChannels,
    targetingConfigSlug: configTargetingConfigSlugs,
  } = useConfig();

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
              {getConfigLabel(firefoxMinVersion, configFirefoxMinVersions)}+
            </div>
            <div>{getConfigLabel(channel, configChannels)}</div>
            <div>
              {getConfigLabel(targetingConfigSlug, configTargetingConfigSlugs)}
            </div>
          </td>
          <td>
            <h3 className="h6">Probe Sets</h3>
            {primaryProbeSets?.length
              ? primaryProbeSets.map((probeSet) => (
                  <div key={probeSet?.name}>{probeSet?.name}</div>
                ))
              : ""}
          </td>
          <td>
            <h3 className="h6">Owner</h3>
            <span>{owner?.email}</span>
          </td>
        </tr>
      </tbody>
    </table>
  );
};

export default TableHighlightsOverview;
