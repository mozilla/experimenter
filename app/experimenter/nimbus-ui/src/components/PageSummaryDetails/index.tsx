/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import { getStatus } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import ExperimentQuickLinks from "../ExperimentQuickLinks";
import Head from "../Head";
import TableSignoff from "../PageSummary/TableSignoff";
import TableAudience from "../Summary/TableAudience";
import TableBranches from "../Summary/TableBranches";
import TableOverview from "../Summary/TableOverview";

type PageSummaryProps = {
  polling?: boolean;
} & RouteComponentProps;

const PageSummaryDetails = ({
  /* istanbul ignore next - only used in tests & stories */
  polling = true,
}: PageSummaryProps) => (
  <AppLayoutWithExperiment
    testId="PageSummary"
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
  const status = getStatus(experiment);
  return (
    <>
      <ExperimentQuickLinks {...{ ...experiment, status }} />

      <Head title={`${experiment.name} – Details`} />

      <h2 className="mt-3 mb-4 h4">Details</h2>

      <div className="d-flex flex-row justify-content-between">
        <h3 className="h5 mb-3">Overview</h3>
      </div>
      <TableOverview {...{ experiment }} />

      <h3 className="h5 mb-3">Audience</h3>
      <TableAudience {...{ experiment }} />

      {/* Branches title is inside its table */}
      <TableBranches {...{ experiment }} />

      {status.launched && (
        <>
          <h3 className="h5 mb-3">
            Actions that were recommended before launch
          </h3>
          <TableSignoff
            signoffRecommendations={experiment.signoffRecommendations}
          />
        </>
      )}
    </>
  );
};

export default PageSummaryDetails;
