/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import React, { useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Badge from "react-bootstrap/Badge";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { useConfig } from "../../hooks";
import { ReactComponent as ExternalIcon } from "../../images/external.svg";
import { SUBMIT_ERROR } from "../../lib/constants";
import { getStatus } from "../../lib/experiment";
import { ConfigOptions, getConfigLabel } from "../../lib/getConfigLabel";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  ExperimentInput,
  NimbusExperimentPublishStatus,
} from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperiment } from "../../types/updateExperiment";
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
  const [submitError, setSubmitError] = useState<string | null>(null);
  const status = getStatus(experiment);
  const branchCount = [
    experiment.referenceBranch,
    ...(experiment.treatmentBranches || []),
  ].filter((branch) => !!branch).length;

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

  const [updateExperiment, { loading: isLoading }] = useMutation<
    { updateExperiment: UpdateExperiment },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  // Set up our collection of status change handlers for review actions
  const [
    onConfirmEndClicked,
    onReviewApprovedClicked,
    onReviewRejectedClicked,
  ] = useMemo(
    () =>
      [
        {
          publishStatus: NimbusExperimentPublishStatus.REVIEW,
        },
        {
          isEndRequested: true,
          publishStatus: NimbusExperimentPublishStatus.APPROVED,
        },
        {
          publishStatus: NimbusExperimentPublishStatus.IDLE,
        },
      ].map(
        (baseDataChanges: Partial<ExperimentInput>) => async (
          _inputEvent?: any,
          submitDataChanges?: Partial<ExperimentInput>,
        ) => {
          try {
            setSubmitError(null);

            const result = await updateExperiment({
              variables: {
                input: {
                  id: experiment.id,
                  ...baseDataChanges,
                  ...submitDataChanges,
                },
              },
            });

            // istanbul ignore next - can't figure out how to trigger this in a test
            if (!result.data?.updateExperiment) {
              throw new Error(SUBMIT_ERROR);
            }

            const { message } = result.data.updateExperiment;

            if (
              message &&
              message !== "success" &&
              typeof message === "object"
            ) {
              return void setSubmitError(message.status.join(", "));
            }

            refetch!();
          } catch (error) {
            setSubmitError(SUBMIT_ERROR);
          }
        },
      ),
    [updateExperiment, experiment, refetch],
  );

  return (
    <div data-testid="summary">
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

      <h2 className="h5 mb-3" data-testid="branches-section-title">
        Branches ({branchCount})
      </h2>
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
