/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useContext } from "react";
import { useScrollToLocationHash } from "../../hooks";
import { ExperimentContext } from "../../lib/contexts";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import Head from "../Head";
import Summary from "../Summary";

const PageSummaryDetails = (props: RouteComponentProps) => {
  const { experiment, refetch, useExperimentPolling } =
    useContext(ExperimentContext)!;
  useExperimentPolling();
  useScrollToLocationHash();
  return (
    <AppLayoutWithExperiment testId="PageSummaryDetails" setHead={false}>
      <Head title={`${experiment.name} – Details`} />

      <h2 className="mt-3 mb-4 h4">Details</h2>
      <Summary {...{ experiment, refetch }} />
    </AppLayoutWithExperiment>
  );
};

export default PageSummaryDetails;
