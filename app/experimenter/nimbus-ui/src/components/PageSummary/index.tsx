/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import TableSummary from "../TableSummary";
import SummaryTimeline from "../SummaryTimeline";

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
    {({ experiment }) => (
      <>
        <h2 className="h5 mb-3">Timeline</h2>
        <SummaryTimeline {...{ experiment }} />

        <h2 className="h5 mb-3">Summary</h2>
        <TableSummary {...{ experiment }} />
      </>
    )}
  </AppLayoutWithExperiment>
);

export default PageSummary;
