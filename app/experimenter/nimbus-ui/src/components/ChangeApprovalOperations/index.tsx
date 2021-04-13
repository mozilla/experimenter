/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import Alert from "react-bootstrap/Alert";
import { ReactComponent as Check } from "../../images/check.svg";
import { humanDate } from "../../lib/dateUtils";
import FormApproveOrReject from "./FormApproveOrReject";
import FormRejectReason from "./FormRejectReason";
import FormRemoteSettingsPending from "./FormRemoteSettingsPending";
import { NimbusChangeLogType } from "./temp-types";

export enum ChangeApprovalOperationsState {
  None,
  ApprovalPending,
  ApproveOrReject,
  RemoteSettingsPending,
  Rejection,
  Rejected,
  TimedOut,
}

export type ChangeApprovalOperationsProps = {
  actionDescription: string;
  isLoading: boolean;
  canReview: boolean;
  reviewRequestEvent?: NimbusChangeLogType;
  approvalEvent?: NimbusChangeLogType;
  rejectionEvent?: NimbusChangeLogType;
  timeoutEvent?: NimbusChangeLogType;
  rejectChange: (fields: { reason: string }) => void;
  approveChange: () => void;
  startRemoteSettingsApproval: () => void;
};

export const ChangeApprovalOperations: React.FC<
  React.PropsWithChildren<ChangeApprovalOperationsProps>
> = ({
  actionDescription,
  isLoading,
  canReview,
  reviewRequestEvent,
  approvalEvent,
  rejectionEvent,
  timeoutEvent,
  rejectChange,
  approveChange,
  startRemoteSettingsApproval,
  children,
}) => {
  let defaultUIState = ChangeApprovalOperationsState.None;
  if (rejectionEvent) {
    defaultUIState = ChangeApprovalOperationsState.Rejected;
  } else if (timeoutEvent) {
    defaultUIState = canReview
      ? ChangeApprovalOperationsState.ApproveOrReject
      : ChangeApprovalOperationsState.ApprovalPending;
  } else if (approvalEvent) {
    defaultUIState = canReview
      ? ChangeApprovalOperationsState.RemoteSettingsPending
      : ChangeApprovalOperationsState.ApprovalPending;
  } else if (reviewRequestEvent) {
    defaultUIState = canReview
      ? ChangeApprovalOperationsState.ApproveOrReject
      : ChangeApprovalOperationsState.ApprovalPending;
  }
  const [uiState, setUIState] = useState<ChangeApprovalOperationsState>(
    defaultUIState,
  );
  const resetDraftUIState = useCallback(() => setUIState(defaultUIState), [
    defaultUIState,
    setUIState,
  ]);

  switch (uiState) {
    case ChangeApprovalOperationsState.ApprovalPending:
      return (
        <Alert
          data-testid="approval-pending"
          variant="success"
          className="bg-transparent text-success"
        >
          <p className="my-1" data-testid="in-review-label">
            <Check className="align-top" /> All set! This experiment will{" "}
            {actionDescription} as soon as it is approved.
          </p>
        </Alert>
      );
    case ChangeApprovalOperationsState.ApproveOrReject:
      return (
        <FormApproveOrReject
          {...{
            actionDescription,
            isLoading,
            timeoutEvent,
            reviewRequestEvent,
            onApprove: async () => {
              await approveChange();
              setUIState(ChangeApprovalOperationsState.RemoteSettingsPending);
            },
            onReject: () => setUIState(ChangeApprovalOperationsState.Rejection),
          }}
        />
      );
    case ChangeApprovalOperationsState.RemoteSettingsPending:
      return (
        <FormRemoteSettingsPending
          {...{
            isLoading,
            onConfirm: startRemoteSettingsApproval,
            actionDescription,
          }}
        />
      );
    case ChangeApprovalOperationsState.Rejection:
      return (
        <FormRejectReason
          {...{
            isLoading,
            onSubmit: rejectChange,
            onCancel: resetDraftUIState,
          }}
        />
      );
    case ChangeApprovalOperationsState.Rejected:
      return (
        <>
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
          {children}
        </>
      );
    default:
      return <>{children}</>;
  }
};

export default ChangeApprovalOperations;
