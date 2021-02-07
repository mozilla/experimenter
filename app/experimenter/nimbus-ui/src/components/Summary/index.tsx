/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import { ReactComponent as ExternalIcon } from "../../images/external.svg";
import { ExperimentContext } from "../../lib/contexts";
import { ConfigOptions, getConfigLabel } from "../../lib/getConfigLabel";
import LinkExternal from "../LinkExternal";
import LinkMonitoring from "../LinkMonitoring";
import NotSet from "../NotSet";
import SummaryTimeline from "./SummaryTimeline";
import TableAudience from "./TableAudience";
import TableBranches from "./TableBranches";
import TableSummary from "./TableSummary";

const Summary = () => {
  const { experiment, status } = useContext(ExperimentContext);
  const {
    slug,
    referenceBranch,
    treatmentBranches,
    monitoringDashboardUrl,
  } = experiment!;

  const branchCount = [referenceBranch, ...(treatmentBranches || [])].filter(
    (branch) => !!branch,
  ).length;

  return (
    <div data-testid="summary">
      <LinkMonitoring {...{ monitoringDashboardUrl }} />

      <h2 className="h5 mb-3">Timeline</h2>
      <SummaryTimeline />

      <div className="d-flex flex-row justify-content-between">
        <h2 className="h5 mb-3">Summary</h2>
        {!status.draft && !status.review && (
          <span>
            <LinkExternal
              href={`/api/v6/experiments/${slug}/`}
              data-testid="link-json"
            >
              <span className="mr-1 align-middle">
                See full JSON representation
              </span>
              <ExternalIcon />
            </LinkExternal>
          </span>
        )}
      </div>
      <TableSummary />

      <h2 className="h5 mb-3">Audience</h2>
      <TableAudience />

      <h2 className="h5 mb-3" data-testid="branches-section-title">
        Branches ({branchCount})
      </h2>
      <TableBranches />
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

export default Summary;
