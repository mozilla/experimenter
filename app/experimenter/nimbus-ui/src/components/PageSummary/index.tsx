/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useState } from "react";
import Alert from "react-bootstrap/Alert";
import { useChangeOperationMutation, useReviewCheck } from "../../hooks";
import { CHANGELOG_MESSAGES } from "../../lib/constants";
import { getStatus } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import ChangeApprovalOperations from "../ChangeApprovalOperations";
import Head from "../Head";
import Summary from "../Summary";
import FormLaunchDraftToPreview from "./FormLaunchDraftToPreview";
import FormLaunchDraftToReview from "./FormLaunchDraftToReview";
import FormLaunchPreviewToReview from "./FormLaunchPreviewToReview";
import getSummaryAction from "./getSummaryAction";
import TableSignoff from "./TableSignoff";

type PageSummaryProps = {
  polling?: boolean;
} & RouteComponentProps;

const PageSummary = ({
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
  refetch: () => void;
}> = ({ experiment, refetch }) => {
  const [showLaunchToReview, setShowLaunchToReview] = useState(false);
  const { invalidPages, InvalidPagesList } = useReviewCheck(experiment);

  const status = getStatus(experiment);

  const {
    isLoading,
    submitError,
    callbacks: [
      onLaunchToPreviewClicked,
      onBackToDraftClicked,
      onLaunchClicked,
      onLaunchReviewApprovedClicked,
      onLaunchReviewRejectedClicked,
      onEndReviewApprovedClicked,
      onEndReviewRejectedClicked,
    ],
  } = useChangeOperationMutation(
    experiment,
    refetch,
    {
      status: NimbusExperimentStatus.PREVIEW,
      changelogMessage: CHANGELOG_MESSAGES.LAUNCHED_TO_PREVIEW,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      changelogMessage: CHANGELOG_MESSAGES.RETURNED_TO_DRAFT,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      statusNext: NimbusExperimentStatus.LIVE,
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      statusNext: NimbusExperimentStatus.LIVE,
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
      changelogMessage: CHANGELOG_MESSAGES.REVIEW_APPROVED,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      statusNext: null,
      publishStatus: NimbusExperimentPublishStatus.IDLE,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      statusNext: NimbusExperimentStatus.COMPLETE,
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
      changelogMessage: CHANGELOG_MESSAGES.REVIEW_APPROVED,
    },
    {
      statusNext: null,
      publishStatus: NimbusExperimentPublishStatus.IDLE,
    },
  );

  const {
    publishStatus,
    canReview,
    reviewRequest: reviewRequestEvent,
    rejection: rejectionEvent,
    timeout: timeoutEvent,
  } = experiment;

  const summaryAction = getSummaryAction(status, experiment.canReview);
  const summaryTitle = summaryAction ? `Summary, ${summaryAction}` : "Summary";

  return (
    <>
      <Head title={`${experiment.name} – ${summaryTitle}`} />

      {submitError && (
        <Alert data-testid="submit-error" variant="warning">
          {submitError}
        </Alert>
      )}

      {summaryAction && <h2 className="mt-3 mb-4 h4">{summaryAction}</h2>}

      {(status.draft || status.preview) && invalidPages.length > 0 ? (
        <Alert variant="warning">
          Before this experiment can be reviewed or launched, all required
          fields must be completed. Fields on the <InvalidPagesList />{" "}
          {invalidPages.length === 1 ? "page" : "pages"} are missing details.
        </Alert>
      ) : (
        <ChangeApprovalOperations
          {...{
            actionDescription: status.live ? "end" : "launch",
            isLoading,
            publishStatus,
            canReview: !!canReview,
            reviewRequestEvent,
            rejectionEvent,
            timeoutEvent,
            rejectChange: status.live
              ? onEndReviewRejectedClicked
              : onLaunchReviewRejectedClicked,
            approveChange: status.live
              ? onEndReviewApprovedClicked
              : onLaunchReviewApprovedClicked,
            reviewUrl: experiment.reviewUrl!,
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
                  onLaunchWithoutPreview: () => setShowLaunchToReview(true),
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

      {!status.launched && (
        <>
          <h3 className="h5 mb-3" data-testid="summary-page-signoff">
            Recommended actions before launch
          </h3>
          <TableSignoff
            signoffRecommendations={experiment.signoffRecommendations}
          />

          <hr />
        </>
      )}

      <h2 className="mt-3 mb-4 h4">Summary</h2>
      <Summary {...{ experiment, refetch }} />
    </>
  );
};

export default PageSummary;
