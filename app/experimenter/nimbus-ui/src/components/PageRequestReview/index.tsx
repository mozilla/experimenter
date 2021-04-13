/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { RouteComponentProps } from "@reach/router";
import React, { useMemo, useRef, useState } from "react";
import Alert from "react-bootstrap/Alert";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { useConfig } from "../../hooks/useConfig";
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

type PageRequestReviewProps = {
  polling?: boolean;
} & RouteComponentProps;

const PageRequestReview = ({
  /* istanbul ignore next - only used in tests & stories */
  polling = true,
}: PageRequestReviewProps) => {
  const { kintoAdminUrl } = useConfig();

  const [submitError, setSubmitError] = useState<string | null>(null);
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();

  const [showLaunchToReview, setShowLaunchToReview] = useState(false);

  const startRemoteSettingsApproval = async () => {
    window.open(kintoAdminUrl!, "_blank");
  };

  const [updateExperiment, { loading: isLoading }] = useMutation<
    { updateExperiment: UpdateExperiment },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  // Set up our collection of status change handlers for review actions
  const [
    onLaunchToPreviewClicked,
    onBackToDraftClicked,
    onLaunchClicked,
    onReviewApprovedClicked,
    onReviewRejectedClicked,
  ] = useMemo(
    () =>
      [
        { status: NimbusExperimentStatus.PREVIEW },
        { status: NimbusExperimentStatus.DRAFT },
        {
          status: NimbusExperimentStatus.DRAFT,
          publishStatus: NimbusExperimentPublishStatus.REVIEW,
        },
        {
          status: NimbusExperimentStatus.DRAFT,
          publishStatus: NimbusExperimentPublishStatus.APPROVED,
        },
        {
          status: NimbusExperimentStatus.DRAFT,
          publishStatus: NimbusExperimentPublishStatus.IDLE,
        },
      ].map((baseDataChanges: Partial<ExperimentInput>) => async (
        inputEvent?: any, // ignored, allows direct use as event handler
        submitDataChanges?: Partial<ExperimentInput>,
      ) => {
        try {
          setSubmitError(null);

          const result = await updateExperiment({
            variables: {
              input: {
                id: currentExperiment.current!.id,
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

          if (message && message !== "success" && typeof message === "object") {
            return void setSubmitError(message.status.join(", "));
          }

          refetchReview.current!();
        } catch (error) {
          console.error(error);
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
        const {
          publishStatus,
          canReview,
          reviewRequest: reviewRequestEvent,
          rejection: rejectionEvent,
          timeout: timeoutEvent,
        } = experiment;

        return (
          <>
            {submitError && (
              <Alert data-testid="submit-error" variant="warning">
                {submitError}
              </Alert>
            )}

            {(status.draft || status.preview) && (
              <ChangeApprovalOperations
                {...{
                  actionDescription: "launch",
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
                {status.draft &&
                  (showLaunchToReview ? (
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
                        onLaunchWithoutPreview: () =>
                          setShowLaunchToReview(true),
                      }}
                    />
                  ))}

                {status.preview && status.idle && (
                  <FormLaunchPreviewToReview
                    {...{
                      isLoading,
                      onSubmit: onLaunchClicked,
                      onBackToDraft: onBackToDraftClicked,
                    }}
                  />
                )}
              </ChangeApprovalOperations>
            )}

            <Summary {...{ experiment }} />
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageRequestReview;
