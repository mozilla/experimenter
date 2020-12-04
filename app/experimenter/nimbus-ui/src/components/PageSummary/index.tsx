/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
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
    sidebar={false}
    {...{ polling }}
  >
    {({ experiment }) => <Summary {...{ experiment }} />}
  </AppLayoutWithExperiment>
);

export default PageSummary;
