/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useRef } from "react";
import Alert from "react-bootstrap/Alert";
import Badge from "react-bootstrap/Badge";
import { useChangeOperationMutation, useConfig } from "../../hooks";
import { ReactComponent as ExternalIcon } from "../../images/external.svg";
import { CHANGELOG_MESSAGES } from "../../lib/constants";
import { getStatus } from "../../lib/experiment";
import { ConfigOptions, getConfigLabel } from "../../lib/getConfigLabel";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentPublishStatus } from "../../types/globalTypes";
import ChangeApprovalOperations from "../ChangeApprovalOperations";
import LinkExternal from "../LinkExternal";
import LinkMonitoring from "../LinkMonitoring";
import NotSet from "../NotSet";
import EndExperiment from "./EndExperiment";
import SummaryTimeline from "./SummaryTimeline";
import TableAudience from "./TableAudience";
import TableBranches from "./TableBranches";
import TableSummary from "./TableSummary";

type SummaryProps = {
  experiment: getExperiment_experimentBySlug;
  refetch?: () => void;
} & Partial<React.ComponentProps<typeof ChangeApprovalOperations>>; // TODO EXP-1143: temporary page-level props, should be replaced by API data for experiment & current user

const Summary = ({ experiment, refetch }: SummaryProps) => {
  const { kintoAdminUrl } = useConfig();
  const status = getStatus(experiment);

  // TODO: PageRequestReview assigns the experiment and refetch values to refs,
  // and since this component shares the same useChangeOperationMutation hook
  // it also needs to pass its experiment/refetch values into refs. Ideally
  // neither of these components need to use refs.
  const currentExperiment = useRef<getExperiment_experimentBySlug>(experiment);
  const refetchReview = useRef<(() => void) | undefined>(refetch);

  const {
    publishStatus,
    canReview,
    reviewRequest: reviewRequestEvent,
    rejection: rejectionEvent,
    timeout: timeoutEvent,
  } = experiment;

  const startRemoteSettingsApproval = async () => {
    window.open(kintoAdminUrl!, "_blank");
  };

  const {
    isLoading,
    submitError,
    callbacks: [
      onConfirmEndClicked,
      onReviewApprovedClicked,
      onReviewRejectedClicked,
    ],
  } = useChangeOperationMutation(
    currentExperiment,
    refetchReview,
    {
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
      isEndRequested: true,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
    },
    {
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
      changelogMessage: CHANGELOG_MESSAGES.END_APPROVED,
    },
    {
      publishStatus: NimbusExperimentPublishStatus.IDLE,
    },
  );

  return (
    <div data-testid="summary" className="mb-5">
      <h2 className="h5 mb-3">
        Timeline
        {status.live && <StatusPills {...{ experiment }} />}
      </h2>

      <SummaryTimeline {...{ experiment }} />

      {submitError && (
        <Alert data-testid="submit-error" variant="warning">
          {submitError}
        </Alert>
      )}

      {status.live && (
        <ChangeApprovalOperations
          {...{
            actionDescription: "end",
            isLoading,
            publishStatus,
            canReview: !!canReview,
            reviewRequestEvent,
            rejectionEvent,
            timeoutEvent,
            rejectChange: onReviewRejectedClicked,
            approveChange: onReviewApprovedClicked,
            startRemoteSettingsApproval,
          }}
        >
          {!experiment.isEndRequested && (
            <EndExperiment {...{ isLoading, onSubmit: onConfirmEndClicked }} />
          )}
        </ChangeApprovalOperations>
      )}

      <hr />

      <LinkMonitoring {...experiment} />

      <div className="d-flex flex-row justify-content-between">
        <h2 className="h5 mb-3">Summary</h2>
        {!status.draft && (
          <span>
            <LinkExternal
              href={`/api/v6/experiments/${experiment.slug}/`}
              data-testid="link-json"
            >
              <span className="mr-1 align-middle">
                See full JSON representation
              </span>
              <ExternalIcon />
            </LinkExternal>
          </span>
        )}
      </div>
      <TableSummary {...{ experiment }} />

      <h2 className="h5 mb-3">Audience</h2>
      <TableAudience {...{ experiment }} />

      {/* Branches title is inside its table */}
      <TableBranches {...{ experiment }} />
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
    {experiment.isEndRequested && (
      <StatusPill
        testId="pill-end-requested"
        label="Experiment End Requested"
      />
    )}
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
