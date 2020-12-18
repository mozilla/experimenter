/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import SummaryTimeline from "../SummaryTimeline";
import TableSummary from "../TableSummary";
import TableAudience from "../TableAudience";
import LinkExternal from "../LinkExternal";
import { getStatus } from "../../lib/experiment";
import MonitoringLink from "../MonitoringLink";
import { getConfigLabel, ConfigOptions } from "../../lib/getConfigLabel";

type SummaryProps = {
  experiment: getExperiment_experimentBySlug;
};

const Summary = ({ experiment }: SummaryProps) => {
  const status = getStatus(experiment);

  return (
    <div data-testid="summary">
      <MonitoringLink {...experiment} />
      <h2 className="h5 mb-3">Timeline</h2>
      <SummaryTimeline {...{ experiment }} />

      <div className="d-flex flex-row justify-content-between">
        <h2 className="h5 mb-3">Summary</h2>
        {!status.draft && !status.review && (
          <span>
            <LinkExternal
              href={`/api/v6/experiments/${experiment.slug}/`}
              data-testid="link-json"
            >
              See full JSON representation
            </LinkExternal>
          </span>
        )}
      </div>
      <TableSummary {...{ experiment }} />

      <h2 className="h5 mb-3">Audience</h2>
      <TableAudience {...{ experiment }} />
    </div>
  );
};

export const displayConfigLabelOrNotSet = (
  value: string | null,
  options: ConfigOptions,
) => {
  if (!value) return <NotSet />;
  return getConfigLabel(value, options);
};

export const NotSet = ({
  "data-testid": testid = "not-set",
}: {
  "data-testid"?: string;
}) => (
  <span className="text-danger" data-testid={testid}>
    Not set
  </span>
);

export default Summary;
