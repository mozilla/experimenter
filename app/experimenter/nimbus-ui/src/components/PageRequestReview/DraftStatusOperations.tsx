/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import Alert from "react-bootstrap/Alert";
import { Config } from "../../hooks/useConfig";
import { ReactComponent as Check } from "../../images/check.svg";
import FormApproveConfirm from "./FormApproveConfirm";
import FormApproveOrRejectLaunch from "./FormApproveOrRejectLaunch";
import FormLaunchDraftToPreview from "./FormLaunchDraftToPreview";
import FormLaunchDraftToReview from "./FormLaunchDraftToReview";
import FormRejectReason from "./FormRejectReason";

export enum DraftStatusOperationsStates {
  DraftToPreview,
  DraftToReview,
  LaunchApprovalPending,
  LaunchApproveOrReject,
  LaunchRejection,
  ApprovalConfirmation,
}

export const DraftStatusOperations = ({
  isLoading,
  featureFlags = { exp1055ReviewFlow: false },
  isLaunchRequested = false, // new experiment property
  launchRequestedByUsername = "", // new experiment property
  currentUsername = "", // new user ID / email property
  currentUserCanApprove = false, // new user permission property
  rejectExperimentLaunch,
  approveExperimentLaunch,
  confirmExperimentLaunchApproval,
  onLaunchClicked,
  onLaunchToPreviewClicked,
}: {
  isLoading: boolean;
  featureFlags: Config["featureFlags"];
  isLaunchRequested: boolean;
  launchRequestedByUsername: string;
  currentUsername: string;
  currentUserCanApprove: boolean;
  rejectExperimentLaunch: (fields: { reason: string }) => void;
  approveExperimentLaunch: () => void;
  confirmExperimentLaunchApproval: () => void;
  onLaunchClicked: () => void;
  onLaunchToPreviewClicked: () => void;
}) => {
  let defaultDraftUIState = DraftStatusOperationsStates.DraftToPreview;
  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  if (featureFlags.exp1055ReviewFlow && isLaunchRequested) {
    if (
      currentUserCanApprove &&
      currentUsername !== launchRequestedByUsername
    ) {
      defaultDraftUIState = DraftStatusOperationsStates.LaunchApproveOrReject;
    } else {
      defaultDraftUIState = DraftStatusOperationsStates.LaunchApprovalPending;
    }
  }

  const [draftUIState, setDraftUIState] = useState<DraftStatusOperationsStates>(
    defaultDraftUIState,
  );

  const resetDraftUIState = useCallback(
    () => setDraftUIState(defaultDraftUIState),
    [defaultDraftUIState, setDraftUIState],
  );

  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  const handleLaunchApprovalClicked = useCallback(async () => {
    await approveExperimentLaunch();
    setDraftUIState(DraftStatusOperationsStates.ApprovalConfirmation);
  }, [approveExperimentLaunch, setDraftUIState]);

  switch (draftUIState) {
    /* istanbul ignore next until EXP-1055 & EXP-1062 done */
    case DraftStatusOperationsStates.LaunchApproveOrReject:
      return (
        <FormApproveOrRejectLaunch
          {...{
            isLoading,
            launchRequestedByUsername,
            onApprove: handleLaunchApprovalClicked,
            onReject: () =>
              setDraftUIState(DraftStatusOperationsStates.LaunchRejection),
          }}
        />
      );

    /* istanbul ignore next until EXP-1055 & EXP-1062 done */
    case DraftStatusOperationsStates.ApprovalConfirmation:
      return (
        <FormApproveConfirm
          {...{
            isLoading,
            onConfirm: confirmExperimentLaunchApproval,
          }}
        />
      );

    /* istanbul ignore next until EXP-1055 & EXP-1062 done */
    case DraftStatusOperationsStates.LaunchRejection:
      return (
        <FormRejectReason
          {...{
            isLoading,
            onSubmit: rejectExperimentLaunch,
            onCancel: resetDraftUIState,
          }}
        />
      );

    /* istanbul ignore next until EXP-1055 & EXP-1062 done */
    case DraftStatusOperationsStates.LaunchApprovalPending:
      return (
        <Alert
          data-testid="submit-success"
          variant="success"
          className="bg-transparent text-success"
        >
          <p className="my-1" data-testid="in-review-label">
            <Check className="align-top" /> All set! This experiment will launch
            as soon as it is approved.
          </p>
        </Alert>
      );

    case DraftStatusOperationsStates.DraftToReview:
      return (
        <FormLaunchDraftToReview
          {...{
            isLoading,
            onSubmit: onLaunchClicked,
            onCancel: resetDraftUIState,
            onLaunchToPreview: onLaunchToPreviewClicked,
          }}
        />
      );

    default:
      return (
        <FormLaunchDraftToPreview
          {...{
            isLoading,
            onSubmit: onLaunchToPreviewClicked,
            onLaunchWithoutPreview: () =>
              setDraftUIState(DraftStatusOperationsStates.DraftToReview),
          }}
        />
      );
  }
};

export default DraftStatusOperations;
