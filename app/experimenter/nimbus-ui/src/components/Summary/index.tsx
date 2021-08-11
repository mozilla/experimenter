/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import Alert from "react-bootstrap/Alert";
import Badge from "react-bootstrap/Badge";
import { LenseContext, useChangeOperationMutation } from "../../hooks";
import { CHANGELOG_MESSAGES } from "../../lib/constants";
import { getStatus } from "../../lib/experiment";
import { ConfigOptions, getConfigLabel } from "../../lib/getConfigLabel";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import LinkMonitoring from "../LinkMonitoring";
import NotSet from "../NotSet";
import TableSignoff from "../PageSummary/TableSignoff";
import PreviewURL from "../PreviewURL";
import EndEnrollment from "./EndEnrollment";
import EndExperiment from "./EndExperiment";
import SummaryTimeline from "./SummaryTimeline";
import TableAudience from "./TableAudience";
import TableBranches from "./TableBranches";
import TableOverview from "./TableOverview";

type SummaryProps = {
  experiment: getExperiment_experimentBySlug;
  refetch?: () => Promise<unknown>;
};

const Summary = ({ experiment, refetch }: SummaryProps) => {
  const status = getStatus(experiment);
  const { isEngineer } = useContext(LenseContext);

  const {
    isLoading,
    submitError,
    callbacks: [onConfirmEndClicked, onConfirmEndEnrollmentClicked],
  } = useChangeOperationMutation(
    experiment,
    refetch,
    {
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
      status: NimbusExperimentStatus.LIVE,
      statusNext: NimbusExperimentStatus.COMPLETE,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
    },
    {
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
      status: NimbusExperimentStatus.LIVE,
      statusNext: NimbusExperimentStatus.LIVE,
      isEnrollmentPaused: true,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
    },
  );

  return (
    <div data-testid="summary" className="mb-5">
      <h3 className="h5 mb-3">
        Timeline
        {status.live && <StatusPills {...{ experiment }} />}
      </h3>

      <SummaryTimeline {...{ experiment }} />

      {submitError && (
        <Alert data-testid="submit-error" variant="warning">
          {submitError}
        </Alert>
      )}

      {status.live &&
        !status.review &&
        !status.pauseRequested &&
        !experiment.isEnrollmentPaused && (
          <EndEnrollment
            {...{ isLoading, onSubmit: onConfirmEndEnrollmentClicked }}
          />
        )}

      {status.live && !status.review && !status.endRequested && (
        <EndExperiment {...{ isLoading, onSubmit: onConfirmEndClicked }} />
      )}

      {isEngineer && (status.live || status.preview) && (
        <PreviewURL {...experiment} status={status} />
      )}

      {status.launched && <LinkMonitoring {...experiment} />}

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

const StatusPills = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => (
  <>
    {experiment.isEnrollmentPaused === false && (
      <StatusPill
        testId="pill-enrolling-active"
        label="Enrolling Users in Progress"
      />
    )}
    {experiment.isEnrollmentPaused && experiment.enrollmentEndDate && (
      <StatusPill
        testId="pill-enrolling-complete"
        label="Enrollment Complete"
      />
    )}
  </>
);

const StatusPill = ({ label, testId }: { label: string; testId: string }) => (
  <Badge
    className="ml-2 border rounded-pill px-2 bg-white border-primary text-primary font-weight-normal"
    data-testid={testId}
  >
    {label}
  </Badge>
);
