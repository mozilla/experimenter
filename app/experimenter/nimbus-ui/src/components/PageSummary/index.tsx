/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import Summary from "../Summary";

type PageRequestReviewProps = {
  polling?: boolean;
} & RouteComponentProps;

const PageSummary: React.FunctionComponent<PageRequestReviewProps> = ({
  polling = true,
}) => (
  <AppLayoutWithExperiment
    testId="PageSummary"
    {...{ polling }}
    analysisRequiredInSidebar
  >
    {({ experiment, refetch }) => <Summary {...{ experiment, refetch }} />}
  </AppLayoutWithExperiment>
);

export default PageSummary;
