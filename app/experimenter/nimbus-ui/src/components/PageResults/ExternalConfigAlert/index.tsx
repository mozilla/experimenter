/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Alert } from "react-bootstrap";
import { humanDate } from "../../../lib/dateUtils";
import { MetadataExternalConfig } from "../../../lib/visualization/types";
import LinkExternal from "../../LinkExternal";

export const ExternalConfigAlert = ({
  externalConfig,
}: {
  externalConfig: MetadataExternalConfig;
}) => (
  <Alert variant="warning" data-testid="external-config-alert">
    <Alert.Heading>Analysis has manual overrides in Jetstream</Alert.Heading>
    <p>
      The results shown on this page are from an analysis ran with at least one
      experiment override that affects only the <em>analysis</em>. The original
      <strong>
        experiment details and description on the Summary page will not reflect
        this.
      </strong>
    </p>
    <ul className="pl-0">
      Overrides (
      <LinkExternal href={externalConfig.url} data-testid="external-config-url">
        click here
      </LinkExternal>{" "}
      to view the config file):
      {externalConfig.start_date && (
        <li className="ml-3" data-testid="external-config-start-date">
          Start date → <strong>{humanDate(externalConfig.start_date)}</strong>
        </li>
      )}
      {externalConfig.end_date && (
        <li className="ml-3" data-testid="external-config-end-date">
          End date → <strong>{humanDate(externalConfig.end_date)}</strong>
        </li>
      )}
      {externalConfig.enrollment_period && (
        <li className="ml-3" data-testid="external-config-enrollment-period">
          Enrollment period →{" "}
          <strong>{externalConfig.enrollment_period} days</strong>
        </li>
      )}
      {externalConfig.reference_branch && (
        <li className="ml-3" data-testid="external-config-reference-branch">
          Baseline branch → <strong>{externalConfig.reference_branch}</strong>
        </li>
      )}
    </ul>
    <p>
      If you have questions about this, please ask data science in{" "}
      <LinkExternal href="https://mozilla.slack.com/archives/C0149JH7C1M">
        #ask-experimenter
      </LinkExternal>
      .
    </p>
  </Alert>
);

export default ExternalConfigAlert;
