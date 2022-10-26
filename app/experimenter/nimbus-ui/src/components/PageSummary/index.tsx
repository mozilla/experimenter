/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useContext, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import { useChangeOperationMutation, useReviewCheck } from "../../hooks";
import { ReactComponent as InfoCircle } from "../../images/info-circle.svg";
import {
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
  LIFECYCLE_REVIEW_FLOWS,
} from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { getStatus, getSummaryAction } from "../../lib/experiment";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../../types/globalTypes";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import ChangeApprovalOperations from "../ChangeApprovalOperations";
import Head from "../Head";
import Summary from "../Summary";
import FormLaunchDraftToPreview from "./FormLaunchDraftToPreview";
import FormLaunchDraftToReview from "./FormLaunchDraftToReview";
import FormLaunchPreviewToReview from "./FormLaunchPreviewToReview";
import TableSignoff from "./TableSignoff";
import Takeaways, { useTakeaways } from "./Takeaways";

const PageSummary = (props: RouteComponentProps) => {
  const { experiment, refetch, useExperimentPolling } =
    useContext(ExperimentContext)!;
  useExperimentPolling();

  const [showLaunchToReview, setShowLaunchToReview] = useState(false);
  const { invalidPages, InvalidPagesList } = useReviewCheck(experiment);
  const takeawaysProps = useTakeaways(experiment, refetch);

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
      onPauseReviewApprovedClicked,
      onPauseReviewRejectedClicked,
    ],
  } = useChangeOperationMutation(
    experiment,
    refetch,
    {
      status: NimbusExperimentStatusEnum.PREVIEW,
      changelogMessage: CHANGELOG_MESSAGES.LAUNCHED_TO_PREVIEW,
    },
    {
      status: NimbusExperimentStatusEnum.DRAFT,
      changelogMessage: CHANGELOG_MESSAGES.RETURNED_TO_DRAFT,
    },
    {
      status: NimbusExperimentStatusEnum.DRAFT,
      statusNext: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW,
    },
    {
      status: NimbusExperimentStatusEnum.DRAFT,
      statusNext: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
      changelogMessage: CHANGELOG_MESSAGES.REVIEW_APPROVED,
    },
    {
      status: NimbusExperimentStatusEnum.DRAFT,
      statusNext: null,
      publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
    },
    {
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: NimbusExperimentStatusEnum.COMPLETE,
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
      changelogMessage: CHANGELOG_MESSAGES.END_APPROVED,
    },
    {
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: null,
      publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
    },
    {
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
      isEnrollmentPaused: true,
      changelogMessage: CHANGELOG_MESSAGES.END_ENROLLMENT_APPROVED,
    },
    {
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: null,
      isEnrollmentPaused: false,
      publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
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

  const {
    rejectChange,
    approveChange,
    buttonTitle: actionButtonTitle,
    description: actionDescription,
  } = useMemo(() => {
    if (status.pauseRequested) {
      return {
        rejectChange: onPauseReviewRejectedClicked,
        approveChange: onPauseReviewApprovedClicked,
        ...LIFECYCLE_REVIEW_FLOWS.PAUSE,
      };
    } else if (status.endRequested) {
      return {
        rejectChange: onEndReviewRejectedClicked,
        approveChange: onEndReviewApprovedClicked,
        ...LIFECYCLE_REVIEW_FLOWS.END,
      };
    } else if (status.draft) {
      return {
        rejectChange: onLaunchReviewRejectedClicked,
        approveChange: onLaunchReviewApprovedClicked,
        ...LIFECYCLE_REVIEW_FLOWS.LAUNCH,
      };
    }
    // HACK: These values shouldn't end up being used, but it makes typechecking happy
    return {
      rejectChange: () => {},
      approveChange: () => {},
      ...LIFECYCLE_REVIEW_FLOWS.NONE,
    };
  }, [
    status,
    onEndReviewApprovedClicked,
    onEndReviewRejectedClicked,
    onLaunchReviewApprovedClicked,
    onLaunchReviewRejectedClicked,
    onPauseReviewApprovedClicked,
    onPauseReviewRejectedClicked,
  ]);

  let launchDocs;
  if (
    summaryAction === LIFECYCLE_REVIEW_FLOWS.LAUNCH.reviewSummary ||
    summaryAction === "Request Launch"
  ) {
    launchDocs = (
      <a
        href={EXTERNAL_URLS.LAUNCH_DOCUMENTATION}
        target="_blank"
        rel="noopener noreferrer"
      >
        <InfoCircle />
      </a>
    );
  }

  return (
    <AppLayoutWithExperiment testId="PageSummary" setHead={false}>
      {status.complete && <Takeaways {...takeawaysProps} />}

      <Head title={`${experiment.name} – ${summaryTitle}`} />

      {submitError && (
        <Alert data-testid="submit-error" variant="warning">
          {submitError}
        </Alert>
      )}

      {summaryAction && (
        <h2 className="mt-3 mb-4 h4">
          {summaryAction} {launchDocs}
        </h2>
      )}

      <ChangeApprovalOperations
        {...{
          actionButtonTitle,
          actionDescription,
          isLoading,
          status,
          // TODO: refactor to just take `experiment` rather than all these separate props?
          publishStatus,
          canReview: !!canReview,
          reviewRequestEvent,
          rejectionEvent,
          timeoutEvent,
          rejectChange,
          approveChange,
          reviewUrl: experiment.reviewUrl!,
          invalidPages,
          InvalidPagesList,
        }}
      >
        {status.draft &&
          !experiment.isArchived &&
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
    </AppLayoutWithExperiment>
  );
};

export default PageSummary;
