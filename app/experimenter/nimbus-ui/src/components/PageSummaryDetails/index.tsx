/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import Head from "../Head";
import Summary from "../Summary";

type PageSummaryProps = {
  polling?: boolean;
} & RouteComponentProps;

const PageSummaryDetails = ({
  /* istanbul ignore next - only used in tests & stories */
  polling = true,
}: PageSummaryProps) => (
  <AppLayoutWithExperiment
    testId="PageSummaryDetails"
    setHead={false}
    {...{ polling }}
  >
    {({ experiment, refetch }) => <PageContent {...{ experiment, refetch }} />}
  </AppLayoutWithExperiment>
);

const PageContent: React.FC<{
  experiment: getExperiment_experimentBySlug;
  refetch: () => Promise<unknown>;
}> = ({ experiment, refetch }) => {
  return (
    <>
      <Head title={`${experiment.name} – Details`} />

      <h2 className="mt-3 mb-4 h4">Details</h2>
      <Summary {...{ experiment, refetch }} />
    </>
  );
};

export default PageSummaryDetails;
