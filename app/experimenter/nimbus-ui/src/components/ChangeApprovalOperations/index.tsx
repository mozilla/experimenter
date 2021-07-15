/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import { EXTERNAL_URLS } from "../../lib/constants";
import { humanDate } from "../../lib/dateUtils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentPublishStatus } from "../../types/globalTypes";
import LinkExternal from "../LinkExternal";
import FormApproveOrReject from "./FormApproveOrReject";
import FormRejectReason from "./FormRejectReason";
import FormRemoteSettingsPending from "./FormRemoteSettingsPending";

export enum ChangeApprovalOperationsState {
  None,
  ApprovalPending,
  ShowFormApproveOrReject,
  ShowFormRejectReason,
  ShowRemoteSettingsPending,
}

export type ChangeApprovalOperationsProps = {
  actionDescription: string;
  isLoading: boolean;
  canReview: boolean;
  publishStatus: getExperiment_experimentBySlug["publishStatus"];
  reviewRequestEvent?: getExperiment_experimentBySlug["reviewRequest"];
  rejectionEvent?: getExperiment_experimentBySlug["rejection"];
  timeoutEvent?: getExperiment_experimentBySlug["timeout"];
  rejectChange: (fields: { changelogMessage: string }) => void;
  approveChange: () => void;
  reviewUrl: string;
};

export const ChangeApprovalOperations: React.FC<
  React.PropsWithChildren<ChangeApprovalOperationsProps>
> = ({
  actionDescription,
  isLoading,
  canReview,
  publishStatus,
  reviewRequestEvent,
  rejectionEvent,
  timeoutEvent,
  rejectChange,
  approveChange,
  reviewUrl,
  children,
}) => {
  const defaultUIState = useMemo(() => {
    switch (publishStatus) {
      case NimbusExperimentPublishStatus.APPROVED:
      case NimbusExperimentPublishStatus.WAITING:
        return canReview
          ? ChangeApprovalOperationsState.ShowRemoteSettingsPending
          : ChangeApprovalOperationsState.ApprovalPending;
      case NimbusExperimentPublishStatus.REVIEW:
        return canReview
          ? ChangeApprovalOperationsState.ShowFormApproveOrReject
          : ChangeApprovalOperationsState.ApprovalPending;
      default:
        return ChangeApprovalOperationsState.None;
    }
  }, [publishStatus, canReview]);

  const [uiState, setUIState] =
    useState<ChangeApprovalOperationsState>(defaultUIState);

  const resetUIState = useCallback(
    () => setUIState(defaultUIState),
    [defaultUIState, setUIState],
  );

  // Whenever publishStatus or canReview changes (i.e. via polling or
  // refetch), override and reset the state.
  useEffect(() => resetUIState(), [resetUIState, publishStatus, canReview]);

  switch (uiState) {
    case ChangeApprovalOperationsState.ApprovalPending:
      return (
        <Alert
          data-testid="approval-pending"
          variant="success"
          className="bg-transparent text-success"
        >
          <p className="my-1" data-testid="in-review-label">
            Please ask someone on your team with review privileges, or a{" "}
            <LinkExternal href={EXTERNAL_URLS.EXPERIMENTER_REVIEWERS}>
              qualified reviewer
            </LinkExternal>
            , to review and {actionDescription} your experiment.{" "}
            <a
              href="#copy"
              className="cursor-copy"
              onClick={(event) => {
                event.preventDefault();
                navigator.clipboard.writeText(window.location.toString());
              }}
            >
              Click here
            </a>{" "}
            to copy the URL to send them.
          </p>
        </Alert>
      );
    case ChangeApprovalOperationsState.ShowFormApproveOrReject:
      return (
        <FormApproveOrReject
          {...{
            actionDescription,
            isLoading,
            timeoutEvent,
            reviewRequestEvent,
            onApprove: async () => {
              await approveChange();
              setUIState(
                ChangeApprovalOperationsState.ShowRemoteSettingsPending,
              );
            },
            onReject: () =>
              setUIState(ChangeApprovalOperationsState.ShowFormRejectReason),
          }}
        />
      );
    case ChangeApprovalOperationsState.ShowRemoteSettingsPending:
      return (
        <FormRemoteSettingsPending
          {...{
            isLoading,
            reviewUrl,
            actionDescription,
          }}
        />
      );
    case ChangeApprovalOperationsState.ShowFormRejectReason:
      return (
        <FormRejectReason
          {...{
            isLoading,
            onSubmit: rejectChange,
            onCancel: resetUIState,
          }}
        />
      );
    default:
      return (
        <>
          {rejectionEvent && (
            <Alert variant="warning" data-testid="rejection-notice">
              <div className="text-body">
                <p className="mb-2">
                  The request to {actionDescription} this experiment was{" "}
                  <strong>Rejected</strong> due to:
                </p>
                <p className="mb-2">
                  {rejectionEvent!.changedBy!.email} on{" "}
                  {humanDate(rejectionEvent!.changedOn!)}:
                </p>
                <p className="bg-white rounded border p-2 mb-0">
                  {rejectionEvent!.message}
                </p>
              </div>
            </Alert>
          )}
          {children}
        </>
      );
  }
};

export default ChangeApprovalOperations;
