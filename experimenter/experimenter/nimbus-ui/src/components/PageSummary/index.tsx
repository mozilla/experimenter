/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import classNames from "classnames";
import React, { useContext, useMemo, useState } from "react";
import { Badge } from "react-bootstrap";
import Alert from "react-bootstrap/Alert";
import AppLayoutWithExperiment from "src/components/AppLayoutWithExperiment";
import ChangeApprovalOperations from "src/components/ChangeApprovalOperations";
import Head from "src/components/Head";
import LinkExternal from "src/components/LinkExternal";
import FormLaunchDraftToPreview from "src/components/PageSummary/FormLaunchDraftToPreview";
import FormLaunchDraftToReview from "src/components/PageSummary/FormLaunchDraftToReview";
import FormLaunchPreviewToReview from "src/components/PageSummary/FormLaunchPreviewToReview";
import Summary from "src/components/Summary";
import SummaryTimeline from "src/components/Summary/SummaryTimeline";
import { useChangeOperationMutation, useReviewCheck } from "src/hooks";
import { ReactComponent as ExternalIcon } from "src/images/external.svg";
import { ReactComponent as InfoCircle } from "src/images/info-circle.svg";
import {
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
  LIFECYCLE_REVIEW_FLOWS,
  QA_STATUS_PROPERTIES,
} from "src/lib/constants";
import { ExperimentContext } from "src/lib/contexts";
import { getStatus, getSummaryAction, StatusCheck } from "src/lib/experiment";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentQAStatusEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

const PageSummary = (props: RouteComponentProps) => {
  const { experiment, refetch, useExperimentPolling } =
    useContext(ExperimentContext)!;
  useExperimentPolling();

  const [showLaunchToReview, setShowLaunchToReview] = useState(false);
  const { invalidPages, InvalidPagesList } = useReviewCheck(experiment);
  const { fieldWarnings } = useReviewCheck(experiment);

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
      onUpdateReviewApprovedClicked,
      onUpdateReviewRejectedClicked,
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
    {
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
      changelogMessage: CHANGELOG_MESSAGES.REVIEW_APPROVED_UPDATE,
    },
    {
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: null,
      publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
      changelogMessage: CHANGELOG_MESSAGES.RETURNED_TO_LIVE,
    },
  );

  const {
    publishStatus,
    qaStatus,
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
    } else if (
      status.updateRequested ||
      status.updateRequestedApproved ||
      status.updateRequestedWaiting
    ) {
      return {
        rejectChange: onUpdateReviewRejectedClicked,
        approveChange: onUpdateReviewApprovedClicked,
        ...LIFECYCLE_REVIEW_FLOWS.UPDATE,
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
    onUpdateReviewApprovedClicked,
    onUpdateReviewRejectedClicked,
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
      <Head title={`${experiment.name} – ${summaryTitle}`} />
      <h5 className="mb-3">
        Timeline
        {status.live && <StatusPills {...{ experiment, status }} />}
        {qaStatus != null &&
          (() => {
            const qaStatusProps = QA_STATUS_PROPERTIES[qaStatus!];
            if (qaStatus !== NimbusExperimentQAStatusEnum.NOT_SET) {
              return (
                <StatusPill
                  testId="pill-qa-status"
                  label={qaStatusProps.description}
                  color={qaStatusProps.className}
                />
              );
            }
          })()}
      </h5>

      <SummaryTimeline {...{ experiment }} />

      {submitError && (
        <Alert data-testid="submit-error" variant="warning">
          {submitError}
        </Alert>
      )}

      {experiment.isRollout &&
        (status.draft || status.preview) &&
        fieldWarnings.bucketing?.length > 0 && (
          <Alert data-testid="bucketing-warning" variant="danger">
            {fieldWarnings.bucketing as SerializerMessage}
            <LinkExternal href={EXTERNAL_URLS.BUCKET_WARNING_EXPLANATION}>
              <span className="mr-1">Learn more</span>
              <ExternalIcon />
            </LinkExternal>
          </Alert>
        )}

      {experiment.isRollout &&
        (experiment.status === NimbusExperimentStatusEnum.DRAFT ||
          experiment.status === NimbusExperimentStatusEnum.PREVIEW) &&
        fieldWarnings.firefox_min_version?.length > 0 && (
          <Alert data-testid="desktop-min-version-warning" variant="warning">
            {fieldWarnings.firefox_min_version as SerializerMessage}
          </Alert>
        )}

      {summaryAction && (
        <h5 className="mt-3 mb-4 ml-3">
          {summaryAction} {launchDocs}
        </h5>
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

      <Summary {...{ experiment, refetch }} />
    </AppLayoutWithExperiment>
  );
};

export default PageSummary;

const StatusPills = ({
  experiment,
  status,
}: {
  experiment: getExperiment_experimentBySlug;
  status: StatusCheck;
}) => (
  <>
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
    {(status.dirty ||
      status.updateRequested ||
      status.updateRequestedApproved ||
      status.updateRequestedWaiting) && (
      <StatusPill
        testId="pill-dirty-unpublished"
        label="Unpublished changes"
        color={"danger"}
      />
    )}
  </>
);

const StatusPill = ({
  label,
  testId,
  color = "primary",
}: {
  label: string;
  testId: string;
  color?: string;
}) => (
  <Badge
    className={classNames(
      `ml-2 border rounded-pill px-2 bg-white font-weight-normal border-${color} text-${color}`,
    )}
    data-testid={testId}
  >
    {label}
  </Badge>
);
