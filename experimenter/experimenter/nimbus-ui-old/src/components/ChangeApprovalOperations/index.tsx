/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import FormApproveOrReject from "src/components/ChangeApprovalOperations/FormApproveOrReject";
import FormRejectReason from "src/components/ChangeApprovalOperations/FormRejectReason";
import FormRemoteSettingsPending from "src/components/ChangeApprovalOperations/FormRemoteSettingsPending";
import RejectionReason from "src/components/ChangeApprovalOperations/RejectionReason";
import LinkExternal from "src/components/LinkExternal";
import { EXTERNAL_URLS } from "src/lib/constants";
import { StatusCheck } from "src/lib/experiment";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import { NimbusExperimentPublishStatusEnum } from "src/types/globalTypes";

export enum ChangeApprovalOperationsState {
  None,
  InvalidPages,
  ApprovalPending,
  ShowFormApproveOrReject,
  ShowFormRejectReason,
  ShowRemoteSettingsPending,
}

export type ChangeApprovalOperationsProps = {
  actionButtonTitle: string;
  actionDescription: string;
  isLoading: boolean;
  canReview: boolean;
  // TODO: refactor to just take `experiment` rather than all these separate props?
  status: StatusCheck;
  publishStatus: getExperiment_experimentBySlug["publishStatus"];
  reviewRequestEvent?: getExperiment_experimentBySlug["reviewRequest"];
  rejectionEvent?: getExperiment_experimentBySlug["rejection"];
  timeoutEvent?: getExperiment_experimentBySlug["timeout"];
  rejectChange: (fields: { changelogMessage: string }) => void;
  approveChange: () => void;
  reviewUrl: string;
  invalidPages: string[];
  InvalidPagesList: React.FC<unknown>;
  ready: boolean;
};

export const ChangeApprovalOperations: React.FC<
  React.PropsWithChildren<ChangeApprovalOperationsProps>
> = ({
  actionButtonTitle,
  actionDescription,
  isLoading,
  canReview,
  status,
  publishStatus,
  reviewRequestEvent,
  rejectionEvent,
  timeoutEvent,
  rejectChange,
  approveChange,
  reviewUrl,
  invalidPages,
  InvalidPagesList,
  children,
  ready,
}) => {
  const defaultUIState = useMemo(() => {
    if (status.archived) {
      // No changes to be approved with an archived experiment
      return ChangeApprovalOperationsState.None;
    }

    if (!ready && status.draft) {
      return ChangeApprovalOperationsState.InvalidPages;
    }

    switch (publishStatus) {
      case NimbusExperimentPublishStatusEnum.APPROVED:
      case NimbusExperimentPublishStatusEnum.WAITING:
        return canReview
          ? ChangeApprovalOperationsState.ShowRemoteSettingsPending
          : ChangeApprovalOperationsState.ApprovalPending;
      case NimbusExperimentPublishStatusEnum.REVIEW:
        return canReview
          ? ChangeApprovalOperationsState.ShowFormApproveOrReject
          : ChangeApprovalOperationsState.ApprovalPending;
      default:
        return ChangeApprovalOperationsState.None;
    }
  }, [status, publishStatus, canReview, ready]);

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
    case ChangeApprovalOperationsState.InvalidPages:
      if (invalidPages.length) {
        return (
          <Alert variant="danger" data-testid="invalid-pages">
            Before this experiment can be reviewed or launched, all required
            fields must be completed. Fields on the <InvalidPagesList />{" "}
            {invalidPages.length === 1 ? "page" : "pages"} are missing details.
          </Alert>
        );
      } else {
        return (
          <Alert variant="danger" data-testid="invalid-internal-error">
            This experiment cannot be launched due to an internal Experimenter
            error. Please ask in #ask-experimenter.
          </Alert>
        );
      }
    case ChangeApprovalOperationsState.ApprovalPending:
      return (
        <Alert
          data-testid="approval-pending"
          variant="success"
          className="bg-transparent text-success"
        >
          <p className="my-1" data-testid="in-review-label">
            Please ask someone on your team with{" "}
            <LinkExternal href={EXTERNAL_URLS.REVIEW_PRIVILIGES}>
              review privileges
            </LinkExternal>{" "}
            or a qualified reviewer to review and {actionDescription}. If you
            don’t have a team reviewer, paste the experiment URL in
            #ask-experimenter and ask for a review to launch your experiment.{" "}
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
            actionButtonTitle,
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
            actionDescription,
            onSubmit: rejectChange,
            onCancel: resetUIState,
          }}
        />
      );
    default: {
      return (
        <>
          {rejectionEvent && <RejectionReason {...{ rejectionEvent }} />}
          {children}
        </>
      );
    }
  }
};

export default ChangeApprovalOperations;
