/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import LinkExternal from "../LinkExternal";

export const LinkMonitoring: React.FC<
  Pick<getExperiment_experimentBySlug, "monitoringDashboardUrl">
> = ({ monitoringDashboardUrl }) => (
  <>
    <h3 className="h5 mb-3" id="monitoring">
      Monitoring
    </h3>
    <p>
      {/* monitoringDashboardUrl won't be null in practice because it's added 
      created at experiment creation time */}
      <LinkExternal
        href={monitoringDashboardUrl!}
        data-testid="link-monitoring-dashboard"
      >
        Click here
      </LinkExternal>{" "}
      to view the live monitoring dashboard.
    </p>
  </>
);

export default LinkMonitoring;
