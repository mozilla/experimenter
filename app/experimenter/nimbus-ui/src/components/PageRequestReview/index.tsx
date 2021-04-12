/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { RouteComponentProps } from "@reach/router";
import React, { useMemo, useRef, useState } from "react";
import Alert from "react-bootstrap/Alert";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { useConfig } from "../../hooks/useConfig";
import { useFakeMutation } from "../../hooks/useFakeMutation";
import { ReactComponent as Check } from "../../images/check.svg";
import { SUBMIT_ERROR } from "../../lib/constants";
import { getStatus } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  ExperimentInput,
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperiment } from "../../types/updateExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import ChangeApprovalOperations from "../ChangeApprovalOperations";
import Summary from "../Summary";
import FormLaunchDraftToPreview from "./FormLaunchDraftToPreview";
import FormLaunchDraftToReview from "./FormLaunchDraftToReview";
import FormLaunchPreviewToReview from "./FormLaunchPreviewToReview";

// Replace with generated type, EXP-1055 & EXP-1062
type RejectFeedback = {
  rejectedByUser: string;
  rejectDate: string;
  rejectReason: string;
} | null;

type PageRequestReviewProps = {
  polling?: boolean;
} & RouteComponentProps &
  Partial<React.ComponentProps<typeof ChangeApprovalOperations>>; // TODO EXP-1143: temporary page-level props, should be replaced by API data for experiment & current user

const PageRequestReview = ({
  /* istanbul ignore next - only used in tests & stories */
  polling = true,
  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  canReview = false,
  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  reviewRequestEvent,
  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  approvalEvent,
  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  rejectionEvent,
  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  timeoutEvent,
}: PageRequestReviewProps) => {
  const { featureFlags } = useConfig();

  const [submitError, setSubmitError] = useState<string | null>(null);
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();

  const [showLaunchToReview, setShowLaunchToReview] = useState(false);

  const [updateExperiment, { loading: updateExperimentLoading }] = useMutation<
    { updateExperiment: UpdateExperiment },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  const [
    rejectExperimentLaunch,
    { loading: rejectExperimentLaunchLoading },
  ] = useFakeMutation();

  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  const [
    approveExperimentLaunch,
    { loading: approveExperimentLaunchLoading },
  ] = useFakeMutation();

  /* istanbul ignore next until EXP-1055 & EXP-1062 done */
  const [
    startRemoteSettingsApproval,
    { loading: startRemoteSettingsApprovalLoading },
  ] = useFakeMutation();

  // TODO: EXP-1062 wrap these new mutations in setSubmitError handling like updateExperiment uses below.

  const isLoading =
    updateExperimentLoading ||
    approveExperimentLaunchLoading ||
    startRemoteSettingsApprovalLoading ||
    rejectExperimentLaunchLoading;

  const [
    onLaunchToPreviewClicked,
    onBackToDraftClicked,
    onLaunchClicked,
  ] = useMemo(
    () =>
      [
        { status: NimbusExperimentStatus.PREVIEW },
        { status: NimbusExperimentStatus.DRAFT },
        {
          status: NimbusExperimentStatus.DRAFT,
          publishStatus: NimbusExperimentPublishStatus.APPROVED,
        },
      ].map((changes: Partial<ExperimentInput>) => async () => {
        try {
          setSubmitError(null);

          const result = await updateExperiment({
            variables: {
              input: { id: currentExperiment.current!.id, ...changes },
            },
          });

          if (!result.data?.updateExperiment) {
            throw new Error(SUBMIT_ERROR);
          }

          const { message } = result.data.updateExperiment;

          if (message && message !== "success" && typeof message === "object") {
            return void setSubmitError(message.status.join(", "));
          }

          refetchReview.current!();
        } catch (error) {
          setSubmitError(SUBMIT_ERROR);
        }
      }),
    [updateExperiment, currentExperiment],
  );

  return (
    <AppLayoutWithExperiment
      title="Review &amp; Launch"
      testId="PageRequestReview"
      {...{ polling }}
      redirect={({ status, review }) => {
        if (review && status.draft && !review.ready) {
          // If the experiment is not ready to be reviewed, let's send them to
          // the first page we know needs fixing up, with field errors displayed
          return `edit/${review.invalidPages[0] || "overview"}?show-errors`;
        }

        if (status.launched) {
          // Return to the experiment root/summary page
          return "";
        }
      }}
    >
      {({ experiment, review }) => {
        currentExperiment.current = experiment;
        refetchReview.current = review.refetch;
        const status = getStatus(experiment);

        return (
          <>
            {submitError && (
              <Alert data-testid="submit-error" variant="warning">
                {submitError}
              </Alert>
            )}

            {status.draft && status.idle && (
              <ChangeApprovalOperations
                {...{
                  actionDescription: "launch",
                  featureFlags,
                  isLoading,
                  canReview,
                  reviewRequestEvent,
                  approvalEvent,
                  rejectionEvent,
                  timeoutEvent,
                  rejectChange: rejectExperimentLaunch,
                  approveChange: approveExperimentLaunch,
                  startRemoteSettingsApproval,
                }}
              >
                {showLaunchToReview ? (
                  <FormLaunchDraftToReview
                    {...{
                      isLoading,
                      onSubmit: onLaunchClicked,
                      onCancel: () => setShowLaunchToReview(false),
                      onLaunchToPreview: onLaunchToPreviewClicked,
                    }}
                  />
                ) : (
                  <FormLaunchDraftToPreview
                    {...{
                      isLoading,
                      onSubmit: onLaunchToPreviewClicked,
                      onLaunchWithoutPreview: () => setShowLaunchToReview(true),
                    }}
                  />
                )}
              </ChangeApprovalOperations>
            )}

            {(status.draft || status.preview) && !status.idle && (
              <Alert
                data-testid="submit-success"
                variant="success"
                className="bg-transparent text-success"
              >
                <p className="my-1" data-testid="in-review-label">
                  <Check className="align-top" /> All set! Your experiment will
                  launch as soon as it is approved.
                </p>
              </Alert>
            )}
            {status.preview && status.idle && (
              <FormLaunchPreviewToReview
                {...{
                  isLoading,
                  onSubmit: onLaunchClicked,
                  onBackToDraft: onBackToDraftClicked,
                }}
              />
            )}

            <Summary {...{ experiment }} />
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageRequestReview;
