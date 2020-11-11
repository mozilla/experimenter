/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import TableSummary from "../TableSummary";

type PageRequestReviewProps = {
  polling?: boolean;
} & RouteComponentProps;

const PageSummary: React.FunctionComponent<PageRequestReviewProps> = ({
  polling = true,
}) => (
  <AppLayoutWithExperiment
    title="Experiment Summary"
    testId="PageSummary"
    sidebar={false}
    {...{ polling }}
  >
    {({ experiment }) => <TableSummary {...{ experiment }} />}
  </AppLayoutWithExperiment>
);

export default PageSummary;
